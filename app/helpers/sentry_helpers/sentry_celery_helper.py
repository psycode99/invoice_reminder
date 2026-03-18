from celery import Task
from sentry_sdk import configure_scope


class SentryHelper(Task):
    def __call__(self, *args, **kwargs):

        request_id = kwargs.get("request_id")
        business_id = kwargs.get("business_id")
        accounting_integration_id = kwargs.get("accounting_integration_id")

        if not business_id and len(args) > 0:
            business_id = args[0]

        if not accounting_integration_id and len(args) > 1:
            accounting_integration_id = args[1]

        if not request_id and len(args) > 2:
            request_id = args[2]

        with configure_scope() as scope:
            if request_id:
                scope.set_tag("request_id", request_id)

            if business_id:
                scope.set_tag("business_id", str(business_id))

            if accounting_integration_id:
                scope.set_tag(
                    "accounting_integration_id", str(accounting_integration_id)
                )

        return self.run(*args, **kwargs)
