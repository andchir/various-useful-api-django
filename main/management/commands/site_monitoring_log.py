from ping3 import ping
from django.core.management.base import BaseCommand, CommandError
from main.models import LogOwnerModel, LogItemModel
import subprocess


class Command(BaseCommand):
    help = 'Site monitoring'

    def add_arguments(self, parser):
        parser.add_argument('--uuid', nargs='?', type=str)

    def handle(self, *args, **options):
        item_uuid = options['uuid'] if 'uuid' in options else None
        if item_uuid is None:
            self.stdout.write(self.style.ERROR('UUID is empty.'))
            return
        item = LogOwnerModel.objects.all().filter(uuid=item_uuid).prefetch_related('log_items').first()

        if item is None:
            self.stdout.write(self.style.ERROR(f'Item not found ({item_uuid}).'))
            return

        log_items = item.log_items.all()
        for log_item in log_items:
            self.stdout.write(self.style.WARNING(f'{log_item.date_created} - {log_item.name} - {log_item.data}'))

        self.stdout.write(self.style.SUCCESS('Done'))
