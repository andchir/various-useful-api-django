from ping3 import ping
import requests
from django.core.management.base import BaseCommand, CommandError
from main.models import LogOwnerModel, LogItemModel
import subprocess

# ping.DEBUG = True


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
            site_url = item.site_url

            if not site_url.startswith('http://') and not site_url.startswith('https://'):
                site_url = 'https://' + site_url

            self.stdout.write(self.style.WARNING(f"\nChecking {site_url}..."))

            resp = requests.head(site_url)

            # ping_seconds = ping(site_host, timeout=5)
            # if ping_seconds is False:
            if resp.status_code != 200:
                self.stdout.write(self.style.ERROR(f"Checking {site_host} FAILED with status {resp.status_code}"))
                result = subprocess.run(restart_command.split(' '), capture_output=True, text=True)
                log_item = LogItemModel(
                    owner=item,
                    name='CRASH',
                    data={'status_code': resp.status_code, 'restart_result': result.stdout}
                )
                log_item.save()
                self.stdout.write(self.style.WARNING(f'Restarted. {result.stdout}'))
            else:
                self.stdout.write(self.style.WARNING(f"Status: {resp.status_code}"))

        self.stdout.write(self.style.SUCCESS('Done'))
