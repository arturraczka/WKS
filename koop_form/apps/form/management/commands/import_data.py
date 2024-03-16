from urllib import request

import tablib
from django.core.management import BaseCommand
from tablib import Dataset

from apps.form.admin import ProducerResource
from apps.user.admin import UserResource
import csv

class Command(BaseCommand):
    help = "export to csvs all data"

    def handle(self, *args, **options):
        my_input_stream = open("data_producder.csv", "r")
        my_dataset = Dataset().load(my_input_stream)
        resource = ProducerResource()
        print(my_dataset)
        dataset = resource.import_data(my_dataset)



