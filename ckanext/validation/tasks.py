from ckan.lib.celery_app import celery

@celery.task(name = "validation.validate")
def validate(dataset_id):
    print dataset_id
