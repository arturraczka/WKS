from django.core.management import BaseCommand

from apps.form.admin import ProducerResource, ProductResource
from apps.user.admin import UserResource, UserProfileResource, UserAdmin
import csv

class Command(BaseCommand):
    help = "export to csvs all data"

    def handle(self, *args, **options):
        resources = [ProducerResource, UserResource, UserProfileResource, ProductResource]
        for resource_class in resources:
            print(resource_class.__name__)
            self._export_to_file(resource_class)


    def _export_to_file(self, resource_class):
        resource = resource_class()
        dataset = resource.export()
        name = resource_class.__name__
        with open(f'data_{name}.csv', 'w', newline='') as csvfile:
            csvfile.write(dataset.csv)



