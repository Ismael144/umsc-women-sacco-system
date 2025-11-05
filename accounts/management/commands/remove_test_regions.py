from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Region, District, Sacco
from django.db.models import Q


class Command(BaseCommand):
    help = 'Remove test regions and keep only actual regions from DOCX files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force deletion without confirmation',
        )

    def handle(self, *args, **options):
        # Get actual region names from DOCX files in the regions folder
        from pathlib import Path
        regions_dir = Path('regions')
        
        if not regions_dir.exists():
            self.stdout.write(self.style.ERROR('Regions directory not found.'))
            return
        
        # Extract region names from DOCX filenames
        actual_regions = []
        for docx_file in regions_dir.glob('*.docx'):
            region_name = docx_file.stem.strip()
            region_name = ' '.join(region_name.split())  # Normalize whitespace
            actual_regions.append(region_name)
        
        if not actual_regions:
            self.stdout.write(self.style.WARNING('No DOCX files found in regions directory.'))
            return
        
        self.stdout.write(f'Found {len(actual_regions)} actual regions from DOCX files.')
        
        # Find test regions (regions not in the actual list)
        all_regions = Region.objects.all()
        test_regions = all_regions.exclude(name__in=actual_regions)
        
        # Also identify common test region patterns (but exclude if they match actual regions)
        test_patterns = [
            'Test Region',
            'Central Region',
            'Western Region',
        ]
        
        # Find regions matching test patterns that are NOT in actual regions
        test_by_pattern = Region.objects.filter(
            (Q(name__in=test_patterns) | 
             Q(name__icontains='test') |
             Q(name__startswith='Test'))
            & ~Q(name__in=actual_regions)
        )
        
        # Combine both - exclude any that are in actual_regions
        test_regions_ids = set()
        for region in test_regions:
            if region.name not in actual_regions:
                test_regions_ids.add(region.id)
        for region in test_by_pattern:
            if region.name not in actual_regions:
                test_regions_ids.add(region.id)
        
        test_regions = Region.objects.filter(id__in=test_regions_ids)
        
        if not test_regions.exists():
            self.stdout.write(self.style.SUCCESS('No test regions found to remove.'))
            return
        
        self.stdout.write(self.style.WARNING(
            f'Found {test_regions.count()} test region(s) to remove:'
        ))
        for region in test_regions:
            # Check if region has saccos
            sacco_count = Sacco.objects.filter(region=region).count()
            district_count = District.objects.filter(region=region).count()
            self.stdout.write(
                f'  - {region.name} (Saccos: {sacco_count}, Districts: {district_count})'
            )
        
        if not options['force']:
            confirm = input('\nAre you sure you want to delete these regions? (yes/no): ')
            if confirm.lower() != 'yes':
                self.stdout.write(self.style.WARNING('Operation cancelled.'))
                return
        
        # Delete test regions (cascade will handle related districts and saccos)
        with transaction.atomic():
            deleted_count = 0
            for region in test_regions:
                # Delete associated districts first
                districts_deleted = District.objects.filter(region=region).delete()[0]
                
                # Delete region (cascade will handle saccos if district is deleted)
                # But we need to update saccos to remove region reference first
                Sacco.objects.filter(region=region).update(region=None)
                
                region.delete()
                deleted_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Deleted region: {region.name} (and {districts_deleted} districts)')
                )
        
        self.stdout.write(self.style.SUCCESS(
            f'\nSuccessfully deleted {deleted_count} test region(s).'
        ))
        
        # Show remaining regions
        remaining = Region.objects.all()
        self.stdout.write(self.style.SUCCESS(
            f'\nRemaining regions ({remaining.count()}):'
        ))
        for region in remaining.order_by('name'):
            self.stdout.write(f'  - {region.name}')

