import ast
import inspect
import typing as t
from pathlib import Path

from pydantic import BaseModel
from pydantic.fields import FieldInfo
from pydantic_core import PydanticUndefined

from acp import schema


class NodeTransformer(ast.NodeTransformer):
    def __init__(self) -> None:
        self._type_import_node: ast.ImportFrom | None = None
        self._schema_import_node: ast.ImportFrom | None = None
        self._should_rewrite = False
        self._literals = {name: value for name, value in schema.__dict__.items() if t.get_origin(value) is t.Literal}

    def _add_typing_import(self, name: str) -> None:
        if not self._type_import_node:
            return
        if not any(alias.name == name for alias in self._type_import_node.names):
            self._type_import_node.names.append(ast.alias(name=name))
            self._should_rewrite = True

    def _add_schema_import(self, name: str) -> None:
        if not self._schema_import_node:
            return
        if not any(alias.name == name for alias in self._schema_import_node.names):
            self._schema_import_node.names.append(ast.alias(name=name))
            self._should_rewrite = True

    def transform(self, source_file: Path) -> None:
        with source_file.open("r", encoding="utf-8") as f:
            source_code = f.read()
        tree = ast.parse(source_code)
        self.visit(tree)
        if self._should_rewrite:
            print("Rewriting signatures in", source_file)
            new_code = ast.unparse(tree)
            with source_file.open("w", encoding="utf-8") as f:
                f.write(new_code)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> ast.AST:
        if node.module == "schema":
            self._schema_import_node = node
        elif node.module == "typing":
            self._type_import_node = node
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        return self.visit_func(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> ast.AST:
        return self.visit_func(node)

    def visit_func(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> ast.AST:
        decorator = next(
            (
                decorator
                for decorator in node.decorator_list
                if isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "param_model"
            ),
            None,
        )
        if not decorator:
            return self.generic_visit(node)
        self._should_rewrite = True
        model_name = t.cast(ast.Name, decorator.args[0]).id
        model = t.cast(type[schema.BaseModel], getattr(schema, model_name))
        param_defaults = [
            self._to_param_def(name, field) for name, field in model.model_fields.items() if name != "field_meta"
        ]
        param_defaults.sort(key=lambda x: x[1] is not None)
        node.args.args[1:] = [param for param, _ in param_defaults]
        node.args.defaults = [default for _, default in param_defaults if default is not None]
        if "field_meta" in model.model_fields:
            node.args.kwarg = ast.arg(arg="kwargs", annotation=ast.Name(id="Any"))
        return self.generic_visit(node)

    def _to_param_def(self, name: str, field: FieldInfo) -> tuple[ast.arg, ast.expr | None]:
        arg = ast.arg(arg=name)
        ann = field.annotation
        if field.default is PydanticUndefined:
            default = None
        elif isinstance(field.default, dict | BaseModel):
            default = ast.Constant(None)
        else:
            default = ast.Constant(value=field.default)
        if ann is not None:
            arg.annotation = self._format_annotation(ann)
        return arg, default

    def _format_annotation(self, annotation: t.Any) -> ast.expr:
        if t.get_origin(annotation) is t.Literal and annotation in self._literals.values():
            name = next(name for name, value in self._literals.items() if value is annotation)
            self._add_schema_import(name)
            return ast.Name(id=name)
        elif (
            inspect.isclass(annotation) and issubclass(annotation, BaseModel) and annotation.__module__ == "acp.schema"
        ):
            self._add_schema_import(annotation.__name__)
            return ast.Name(id=annotation.__name__)
        elif args := t.get_args(annotation):
            origin = t.get_origin(annotation)
            return ast.Subscript(
                value=self._format_annotation(origin),
                slice=ast.Tuple(elts=[self._format_annotation(arg) for arg in args], ctx=ast.Load())
                if len(args) > 1
                else self._format_annotation(args[0]),
                ctx=ast.Load(),
            )
        elif annotation.__module__ == "typing":
            name = annotation.__name__
            self._add_typing_import(name)
            return ast.Name(id=name)
        elif annotation is None or annotation is type(None):
            return ast.Constant(value=None)
        elif annotation in __builtins__.values():
            return ast.Name(id=annotation.__name__)
        else:
            print(f"Warning: Unhandled annotation type: {annotation}")
            self._add_typing_import("Any")
            return ast.Name(id="Any")


def gen_signature(source_dir: Path) -> None:
    import importlib

    importlib.reload(schema)  # Ensure schema is up to date
    for source_file in source_dir.rglob("*.py"):
        transformer = NodeTransformer()
        transformer.transform(source_file)
