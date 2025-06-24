from datetime import datetime, timezone, timedelta
from .base import BaseSeeder
from app.models import (
    Community, Lead, Conversation, Unit, PetPolicy, 
    TourSlot, Message, UnitPricing, ActionType, PetType
)
import random

class Seeder(BaseSeeder):
    def seed(self, session):
        communities = self.create_communities(session)
        leads = self.create_leads(session)
        units = self.create_units(session, communities)
        self.create_pet_policies(session, communities)
        tour_slots = self.create_tour_slots(session, communities)
        conversations = self.create_conversations(session, leads, communities)
        self.create_unit_pricing(session, units)
        self.create_messages(session, conversations, tour_slots)
        
    def create_communities(self, session):
        communities_data = [
            {
                "name": "Sunset Gardens Apartments",
                "address": "1234 Maple Avenue, Springfield, IL 62701",
                "phone": "(555) 123-4567",
                "email": "leasing@sunsetgardens.com"
            },
            {
                "name": "The Oaks at Riverside",
                "address": "567 Oak Boulevard, Austin, TX 78701",
                "phone": "(555) 234-5678", 
                "email": "info@oaksriverside.com"
            },
            {
                "name": "Metro Heights",
                "address": "890 Downtown Street, Denver, CO 80202",
                "phone": "(555) 345-6789",
                "email": "leasing@metroheights.com"
            },
            {
                "name": "Willow Creek Village",
                "address": "456 Willow Lane, Portland, OR 97201",
                "phone": "(555) 456-7890",
                "email": "rentals@willowcreek.com"
            }
        ]
        
        communities = []
        for data in communities_data:
            existing = session.query(Community).filter_by(name=data["name"]).first()
            if not existing:
                community = Community(**data)
                session.add(community)
                session.flush()
                communities.append(community)
            else:
                communities.append(existing)
                
        return communities
        
    def create_leads(self, session):
        leads_data = [
            {
                "name": "Sarah Johnson",
                "email": "sarah.johnson@email.com",
                "phone": "(555) 111-2222",
                "preferred_bedrooms": 2,
                "preferred_move_in": datetime.now(timezone.utc) + timedelta(days=30)
            },
            {
                "name": "Michael Chen",
                "email": "m.chen@email.com", 
                "phone": "(555) 222-3333",
                "preferred_bedrooms": 1,
                "preferred_move_in": datetime.now(timezone.utc) + timedelta(days=45)
            },
            {
                "name": "Jessica Martinez",
                "email": "jessica.martinez@email.com",
                "phone": "(555) 333-4444",
                "preferred_bedrooms": 3,
                "preferred_move_in": datetime.now(timezone.utc) + timedelta(days=60)
            },
            {
                "name": "David Park",
                "email": "david.park@email.com",
                "phone": "(555) 444-5555",
                "preferred_bedrooms": 2,
                "preferred_move_in": datetime.now(timezone.utc) + timedelta(days=15)
            },
            {
                "name": "Emily Rodriguez",
                "email": "emily.r@email.com",
                "phone": "(555) 555-6666",
                "preferred_bedrooms": 1,
                "preferred_move_in": datetime.now(timezone.utc) + timedelta(days=90)
            }
        ]
        
        leads = []
        for data in leads_data:
            existing = session.query(Lead).filter_by(email=data["email"]).first()
            if not existing:
                lead = Lead(**data)
                session.add(lead)
                session.flush()
                leads.append(lead)
            else:
                leads.append(existing)
                
        return leads
        
    def create_units(self, session, communities):
        units = []
        
        for community in communities:
            unit_configs = [
                (1, 1.0, 650, 1200, "Studio apartment with modern appliances"),
                (1, 1.0, 750, 1350, "One bedroom with balcony and city view"),
                (1, 1.0, 700, 1300, "Cozy one bedroom with updated kitchen"),
                (2, 1.5, 950, 1800, "Two bedroom with spacious living area"),
                (2, 2.0, 1100, 2100, "Two bedroom with walk-in closets"),
                (2, 2.0, 1050, 1950, "Two bedroom with in-unit washer/dryer"),
                (3, 2.0, 1350, 2800, "Three bedroom townhouse style"),
                (3, 2.5, 1400, 2950, "Three bedroom with master suite")
            ]
            
            for i, (bedrooms, bathrooms, sqft, rent, desc) in enumerate(unit_configs):
                unit_number = f"{bedrooms}{chr(65 + i)}{random.randint(1, 9)}"
                available_date = datetime.now(timezone.utc) + timedelta(days=random.randint(0, 120))
                
                unit = Unit(
                    community_id=community.id,
                    unit_number=unit_number,
                    bedrooms=bedrooms,
                    bathrooms=bathrooms,
                    square_feet=sqft,
                    description=desc,
                    base_rent=rent,
                    is_available=random.choice([True, True, True, False]),
                    available_date=available_date if random.choice([True, False]) else None
                )
                session.add(unit)
                session.flush()
                units.append(unit)
                
        return units
        
    def create_pet_policies(self, session, communities):
        for community in communities:
            pet_policies = [
                {
                    "pet_type": PetType.DOG,
                    "allowed": True,
                    "fee": 300,
                    "deposit": 500,
                    "monthly_rent": 50,
                    "max_count": 2,
                    "weight_limit": 75,
                    "notes": "Breed restrictions apply. Must be house trained."
                },
                {
                    "pet_type": PetType.CAT,
                    "allowed": True,
                    "fee": 200,
                    "deposit": 300,
                    "monthly_rent": 35,
                    "max_count": 2,
                    "weight_limit": None,
                    "notes": "Must be spayed/neutered and up to date on vaccinations."
                },
                {
                    "pet_type": PetType.BIRD,
                    "allowed": True,
                    "fee": 100,
                    "deposit": 150,
                    "monthly_rent": 15,
                    "max_count": 3,
                    "weight_limit": None,
                    "notes": "Caged birds only."
                },
                {
                    "pet_type": PetType.FISH,
                    "allowed": True,
                    "fee": 0,
                    "deposit": 0,
                    "monthly_rent": 0,
                    "max_count": None,
                    "weight_limit": None,
                    "notes": "Aquarium size limited to 50 gallons."
                }
            ]
            
            for policy_data in pet_policies:
                policy = PetPolicy(community_id=community.id, **policy_data)
                session.add(policy)
                
    def create_tour_slots(self, session, communities):
        tour_slots = []
        base_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        for community in communities:
            for day_offset in range(0, 14):
                date = base_date + timedelta(days=day_offset)
                
                if date.weekday() < 5:  # Weekdays
                    time_slots = [(10, 0), (11, 30), (13, 0), (14, 30), (16, 0)]
                else:  # Weekends
                    time_slots = [(10, 0), (12, 0), (14, 0), (16, 0)]
                    
                for hour, minute in time_slots:
                    start_time = date.replace(hour=hour, minute=minute)
                    end_time = start_time + timedelta(hours=1)
                    
                    slot = TourSlot(
                        community_id=community.id,
                        start_time=start_time,
                        end_time=end_time,
                        is_available=random.choice([True, True, True, False]),
                        max_capacity=random.choice([1, 2, 3]),
                        current_bookings=random.randint(0, 1)
                    )
                    session.add(slot)
                    session.flush()
                    tour_slots.append(slot)
                    
        return tour_slots
        
    def create_conversations(self, session, leads, communities):
        conversations = []
        
        for i, lead in enumerate(leads[:4]):
            community = communities[i % len(communities)]
            
            conversation = Conversation(
                lead_id=lead.id,
                community_id=community.id
            )
            session.add(conversation)
            session.flush()
            conversations.append(conversation)
            
        return conversations
        
    def create_unit_pricing(self, session, units):
        for unit in units:
            base_date = datetime.now(timezone.utc)
            
            for month_offset in range(0, 6):
                move_in_date = base_date + timedelta(days=30 * month_offset)
                
                rent_variation = random.randint(-100, 200)
                rent = unit.base_rent + rent_variation
                
                special_offers = [
                    None,
                    "First month free",
                    "No security deposit",
                    "50% off first month",
                    "Free parking for 6 months"
                ]
                
                special_offer = random.choice(special_offers)
                special_discount = random.randint(50, 500) if special_offer else None
                
                pricing = UnitPricing(
                    unit_id=unit.id,
                    move_in_date=move_in_date,
                    rent=rent,
                    special_offer=special_offer,
                    special_discount=special_discount,
                    expires_date=move_in_date + timedelta(days=30) if special_offer else None
                )
                session.add(pricing)
                
    def create_messages(self, session, conversations, tour_slots):
        sample_messages = [
            "Hi! I'm interested in a 2-bedroom apartment. What do you have available?",
            "Can you tell me about your pet policy? I have a small dog.",
            "I'd like to schedule a tour for this weekend if possible.",
            "What amenities are included in the rent?",
            "Do you have any move-in specials right now?",
            "Is parking included or is there an additional fee?",
            "What's the application process like?",
            "Are utilities included in the rent?"
        ]
        
        sample_replies = [
            "Thank you for your interest! I'd be happy to help you find the perfect apartment.",
            "We have several 2-bedroom units available. Would you like to schedule a tour?",
            "Our pet policy allows dogs with a deposit. Let me get you the details.",
            "I can schedule a tour for you this weekend. What time works best?",
            "We currently have a great move-in special - first month half off!",
            "Parking is available for an additional $75 per month.",
            "The application process is simple and can be completed online."
        ]
        
        for i, conversation in enumerate(conversations):
            num_messages = random.randint(2, 5)
            
            for msg_num in range(num_messages):
                message_text = random.choice(sample_messages)
                reply_text = random.choice(sample_replies) if msg_num > 0 else None
                
                action = None
                proposed_time = None
                
                if "tour" in message_text.lower() and tour_slots:
                    action = ActionType.PROPOSE_TOUR
                    proposed_time = random.choice(tour_slots).start_time
                elif msg_num == num_messages - 1 and random.choice([True, False]):
                    action = random.choice([ActionType.ASK_CLARIFICATION, ActionType.HANDOFF_HUMAN])
                
                message = Message(
                    conversation_id=conversation.id,
                    message_text=message_text,
                    reply_text=reply_text,
                    action=action,
                    proposed_time=proposed_time,
                    tools_called={"search_units": True} if "bedroom" in message_text else None,
                    llm_tokens_used=random.randint(150, 800),
                    llm_latency_ms=random.randint(200, 1500),
                    request_id=f"req_{i}_{msg_num}_{random.randint(1000, 9999)}"
                )
                session.add(message)