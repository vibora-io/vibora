import json


class TemplateError(Exception):
    pass


class TemplateRenderError(TemplateError):
    def __init__(self, template, template_line, exception, template_name):
        self.template = template
        self.original_exception = exception
        self.template_line = template_line
        super().__init__(
            json.dumps(
                {
                    "template_line": template_line,
                    "error": str(exception),
                    "template_name": template_name,
                }
            )
        )


class DuplicatedTemplateName(TemplateError):
    pass


class MissingEnvironment(TemplateError):
    pass


class TemplateNotFound(TemplateError):
    pass


class InvalidTag(TemplateError):
    pass


class InvalidExpression(TemplateError):
    pass


class FailedToCompileTemplate(TemplateError):
    pass


class ConflictingNames(TemplateError):
    pass


class InvalidVersion(TemplateError):
    pass


class InvalidArchitecture(TemplateError):
    pass
