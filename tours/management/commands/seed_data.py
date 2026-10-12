from django.core.management.base import BaseCommand
from django.contrib.auth.models import User as DjangoUser
from tours.models import Package, Booking, TripPlan, ContactMessage, CustomerUser
from django.db import connection


class Command(BaseCommand):
    help = 'Seed initial packages, superuser, and sync legacy data'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Seeding tour packages...'))

        packages_data = [
            {
                'id': 1,
                'title': 'Bali Island Escape',
                'duration': '5 DAYS · BALI',
                'location': 'Bali, Indonesia',
                'description': 'Beaches, temples, sunsets and private island experiences.',
                'price': 39999.00,
                'image_url': 'https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1000&q=85',
                'featured': True,
                'itinerary': 'Day 1: Arrival & Sunset at Uluwatu Temple\nDay 2: Ubud Art Villages, Monkey Forest & Rice Terraces\nDay 3: Nusa Penida Island Speedboat Tour & Kelingking Beach\nDay 4: Mount Batur Sunrise Trek & Hot Springs\nDay 5: Seminyak Beach Club & Departure',
                'inclusions': '4-Star Beach Resort Stays\nDaily Buffet Breakfast\nAirport Pick & Drop Transfers\nEnglish Speaking Tour Guide\nNusa Penida Ferry Tickets'
            },
            {
                'id': 2,
                'title': 'Paris & Swiss Dreams',
                'duration': '7 DAYS · EUROPE',
                'location': 'Paris & Switzerland',
                'description': 'Elegant city walks, Alpine views and unforgettable rail journeys.',
                'price': 129999.00,
                'image_url': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?auto=format&fit=crop&w=1000&q=85',
                'featured': True,
                'itinerary': 'Day 1: Arrival in Paris & Seine River Cruise\nDay 2: Eiffel Tower 2nd Level & Louvre Museum Tour\nDay 3: TGV High Speed Train from Paris to Zurich\nDay 4: Mount Titlis Cable Car & Ice Flyer Experience\nDay 5: Lucerne Walking Tour & Lake Cruise\nDay 6: Interlaken & Jungfraujoch Top of Europe\nDay 7: Departure from Zurich',
                'inclusions': 'Premium Hotel Stays in Paris & Lucerne\nSwiss Rail Travel Pass Included\nDaily European Breakfast\nAll Landmark Entry Tickets & Cable Cars'
            },
            {
                'id': 3,
                'title': 'Dubai Luxe Weekend',
                'duration': '6 DAYS · DUBAI',
                'location': 'Dubai, UAE',
                'description': 'Skyline views, desert safari, shopping and premium dining.',
                'price': 54999.00,
                'image_url': 'https://images.unsplash.com/photo-1539650116574-75c0c6d73f6e?auto=format&fit=crop&w=1000&q=85',
                'featured': True,
                'itinerary': 'Day 1: Arrival, Dhow Cruise Dinner at Dubai Marina\nDay 2: Half Day Dubai City Tour + Dubai Frame\nDay 3: Burj Khalifa 124th Floor & Dubai Mall Fountain Show\nDay 4: Luxury 4x4 Desert Safari with BBQ Dinner & Belly Dance\nDay 5: Miracle Garden & Global Village\nDay 6: Souk Shopping & Departure',
                'inclusions': '5-Star Hotel Stay with Breakfast\nPrivate Airport Transfers\nDesert Safari with BBQ & Entertainment\nBurj Khalifa Observation Deck Tickets'
            },
            {
                'id': 4,
                'title': 'Kashmir Serenity',
                'duration': '6 DAYS · KASHMIR',
                'location': 'Kashmir, India',
                'description': 'Dal Lake, mountains, valleys and peaceful local experiences.',
                'price': 28999.00,
                'image_url': 'https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?auto=format&fit=crop&w=1000&q=85',
                'featured': True,
                'itinerary': 'Day 1: Arrival in Srinagar & Shikara Ride on Dal Lake\nDay 2: Srinagar to Gulmarg - Gondola Cable Car Ride\nDay 3: Gulmarg to Pahalgam Valley of Shepherds\nDay 4: Pahalgam Sightseeing (Betaab & Aru Valley)\nDay 5: Return to Srinagar - Mughal Gardens & Local Markets\nDay 6: Houseboat Breakfast & Departure',
                'inclusions': 'Deluxe Houseboat & 4-Star Resort Stays\nBreakfast & Dinner Included (MAP Plan)\nPrivate Sedan Vehicle for All Sightseeing\nShikara Ride on Dal Lake Included'
            },
            {
                'id': 5,
                'title': 'Maldives Luxury Overwater Escape',
                'duration': '5 DAYS · MALDIVES',
                'location': 'Maldives',
                'description': 'Crystal turquoise lagoons, private overwater villa & coral reef snorkeling.',
                'price': 74999.00,
                'image_url': 'https://images.unsplash.com/photo-1514282401047-d79a71a590e8?auto=format&fit=crop&w=1000&q=85',
                'featured': False,
                'itinerary': 'Day 1: Arrival at Male Airport & Speedboat Transfer to Island Resort\nDay 2: Overwater Villa Leisure, Sunset Dolphin Cruise\nDay 3: Guided Snorkeling Coral Safari & Watersports\nDay 4: Spa Treatment & Romantic Candlelight Beach Dinner\nDay 5: Island Sunrise & Speedboat Return to Airport',
                'inclusions': 'Overwater Villa Accommodation\nAll Inclusive Meals & Drinks\nRoundtrip Speedboat Transfers\nComplimentary Snorkeling Equipment'
            },
            {
                'id': 6,
                'title': 'Royal Rajasthan Heritage',
                'duration': '6 DAYS · RAJASTHAN',
                'location': 'Jaipur, Udaipur & Jodhpur',
                'description': 'Majestic palaces, royal fortresses, camel desert safari & vibrant culture.',
                'price': 32999.00,
                'image_url': 'https://images.unsplash.com/photo-1599661046289-e31897846e41?auto=format&fit=crop&w=1000&q=85',
                'featured': False,
                'itinerary': 'Day 1: Arrival in Jaipur - Amer Fort & Jal Mahal\nDay 2: City Palace, Hawa Mahal & Travel to Jodhpur\nDay 3: Mehrangarh Fort & Umaid Bhawan Palace\nDay 4: Travel to Udaipur via Ranakpur Jain Temple\nDay 5: Udaipur Lake Pichola Boat Ride & City Palace\nDay 6: Saheliyon-ki-Bari & Departure',
                'inclusions': 'Heritage Haveli & Palace Stays\nDaily Breakfast & Cultural Dinner\nDedicated AC Tourist Coach\nAll Monument Entrance Permits'
            }
        ]

        for pdata in packages_data:
            pkg, created = Package.objects.update_or_create(
                id=pdata['id'],
                defaults=pdata
            )
            status_str = 'Created' if created else 'Updated'
            self.stdout.write(f" - {status_str} package: {pkg.title}")

        # Seed Django Superuser
        admin_email = 'admin@deluxtour.com'
        if not DjangoUser.objects.filter(username='admin').exists():
            DjangoUser.objects.create_superuser('admin', admin_email, 'Admin@123')
            self.stdout.write(self.style.SUCCESS(" - Created superuser 'admin' with password 'Admin@123'"))
        else:
            self.stdout.write(" - Superuser 'admin' already exists.")

        # Sync legacy users into CustomerUser if needed
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT FullName, Email, PasswordHash, PasswordSalt, CreatedAt FROM users")
                rows = cursor.fetchall()
                for full_name, email, p_hash, p_salt, created_at in rows:
                    if not CustomerUser.objects.filter(email=email).exists():
                        CustomerUser.objects.create(
                            full_name=full_name,
                            email=email,
                            password_hash=p_hash,
                            password_salt=p_salt or '',
                            created_at=created_at
                        )
                        self.stdout.write(f" - Synced legacy user: {email}")
        except Exception as e:
            self.stdout.write(f" - Note on legacy users sync: {e}")

        self.stdout.write(self.style.SUCCESS("All seed data successfully applied!"))
