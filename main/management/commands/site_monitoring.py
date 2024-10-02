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
        items = LogOwnerModel.objects.all().filter(uuid=item_uuid) \
            if item_uuid \
            else LogOwnerModel.objects.all()

        if len(items) == 0:
            self.stdout.write(self.style.ERROR(f'Item not found ({item_uuid}).'))
            return

        for item in items:
            if item.site_url is None or item.data is None:
                continue
            restart_command = item.data['restart_command'] if 'restart_command' in item.data else ''
            if not restart_command:
                continue
            site_host = item.site_url.replace('http://', '').replace('https://', '').split('/')[0]
            ping_seconds = ping(site_host, timeout=5)
            if ping_seconds is False:
                self.stdout.write(self.style.ERROR(f"Ping {site_host}: FAIL"))
                result = subprocess.run(restart_command.split(' '), capture_output=True, text=True)
                log_item = LogItemModel(owner=item, name='CRASH', data={'restart_result': result.stdout})
                log_item.save()
                self.stdout.write(self.style.WARNING(result.stdout))
            else:
                self.stdout.write(self.style.WARNING(f"Ping {site_host}: {ping_seconds}"))

        self.stdout.write(self.style.SUCCESS('Done'))
