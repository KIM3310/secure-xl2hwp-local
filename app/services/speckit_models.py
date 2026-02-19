from typing import Literal, Union

from pydantic import BaseModel, Field

ScalarType = Literal["string", "int", "float", "date", "bool"]


class FieldSpec(BaseModel):
    name: str
    key: str
    type: ScalarType = "string"
    required: bool = False
    pii: bool = False


class ConstraintSpec(BaseModel):
    unique: list[str] = Field(default_factory=list)
    non_negative: list[str] = Field(default_factory=list)


class TemplateSpec(BaseModel):
    placeholders: dict[str, str] = Field(default_factory=dict)


class DataContract(BaseModel):
    version: str = "1.0"
    dataset: str
    fields: list[FieldSpec]
    constraints: ConstraintSpec = Field(default_factory=ConstraintSpec)
    templates: dict[str, TemplateSpec] = Field(default_factory=dict)


class RegexReplaceRule(BaseModel):
    column: str
    pattern: str
    replacement: str = ""


class DerivedColumnRule(BaseModel):
    name: str
    expression: str


class CleanupProfile(BaseModel):
    profile_name: str
    sheet_name: Union[str, int] = 0
    rename_columns: dict[str, str] = Field(default_factory=dict)
    drop_columns: list[str] = Field(default_factory=list)
    required_columns: list[str] = Field(default_factory=list)
    type_cast: dict[str, ScalarType] = Field(default_factory=dict)
    fill_defaults: dict[str, Union[str, int, float, bool]] = Field(default_factory=dict)
    regex_replace: list[RegexReplaceRule] = Field(default_factory=list)
    derived_columns: list[DerivedColumnRule] = Field(default_factory=list)
    template_mapping: dict[str, str] = Field(default_factory=dict)


class TemplatePlaceholderRule(BaseModel):
    source: str
    transform: str = "identity"
    default: Union[str, int, float, bool, None] = None


class TemplateTableSectionRule(BaseModel):
    placeholder: str
    columns: list[str]
    row_template: str
    max_rows: int = 30
    empty_text: str = "-"


class HancomTemplateProfile(BaseModel):
    template_name: str
    placeholder_rules: dict[str, TemplatePlaceholderRule] = Field(default_factory=dict)
    table_sections: list[TemplateTableSectionRule] = Field(default_factory=list)
    include_unmapped_placeholders: bool = True


class UserSpec(BaseModel):
    user_id: str
    role: str
    password_hash: str
    active: bool = True


class UserRegistry(BaseModel):
    users: list[UserSpec] = Field(default_factory=list)
