import sys

from seeds.seeds import Seeder
from app.config import settings


def seed_database():
    seeder = Seeder()
    seeder.run()
    print("Seeding completed")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "seed":
        seed_database()