import json
import random
from datetime import datetime

def extract_coordinates(coordinates_array):
    """Extract lat/lng from coordinates array"""
    if coordinates_array and len(coordinates_array) > 0 and len(coordinates_array[0]) == 2:
        lng, lat = coordinates_array[0]
        return lat, lng
    return None, None

def convert_venue_to_mongo(venue_data):
    """Convert venue JSON structure to MongoDB catering vendor structure"""
    
    # Extract coordinates
    lat, lng = extract_coordinates(venue_data.get('coordinates', []))
    
    # Map cover images - include all images starting with https://partyslate
    cover_images = []
    if venue_data.get('coverImages'):
        for img in venue_data.get('coverImages', []):
            img_path = img.get('imagePath', '')
            if img_path.startswith('https://partyslate'):
                cover_images.append(img_path)
    
    # Create slug from name
    slug = venue_data.get('slug', venue_data.get('name', '').lower().replace(' ', '-').replace(',', ''))
    
    # Map event types from eventTypeCounts
    serve_events = []
    event_counts = venue_data.get('eventTypeCounts', {})
    event_mapping = {
        'wedding': 'wedding',
        'corporateEvent': 'corporate',
        'corporateHolidayParty': 'corporate',
        'milestoneBirthday': 'birthday',
        'kidsBirthday': 'birthday',
        '1stBirthday': 'birthday',
        'anniversary': 'anniversary',
        'graduationParty': 'graduation'
    }
    
    for event_type, count in event_counts.items():
        if count > 0 and event_type in event_mapping:
            mapped_event = event_mapping[event_type]
            if mapped_event not in serve_events:
                serve_events.append(mapped_event)
    
    # If no events found, add default ones
    if not serve_events:
        serve_events = ['wedding', 'corporate', 'birthday']
    
    # Extract address components (basic parsing)
    address = venue_data.get('formattedAddress', '')
    address_parts = address.split(', ')
    
    line_one = address_parts[0] if len(address_parts) > 0 else ''
    city = address_parts[1] if len(address_parts) > 1 else ''
    state_zip = address_parts[2].split(' ') if len(address_parts) > 2 else ['', '']
    state = state_zip[0] if len(state_zip) > 0 else ''
    zip_code = state_zip[1] if len(state_zip) > 1 else ''
    
    # Generate random business start year
    business_start_year = random.randint(2010, 2020)
    
    # Calculate rating and review count from testimonials
    review_count = len(venue_data.get('clientTestimonials', []))
    rating = round(random.uniform(4.0, 5.0), 1)  # Generate realistic rating
    
    # Generate budget range ($5,000 to $50,000)
    budget_min = random.randint(5000, 25000)  # Min budget between $5k-$25k
    budget_max = random.randint(budget_min + 5000, 50000)  # Max budget at least $5k higher, up to $50k
    
    mongo_structure = {
        "profileImage": venue_data.get('brandImagePath', venue_data.get('coverImagePath', '')),
        "coverImages": cover_images,
        "isApproved": True,
        "vendorType": "venue",  # Changed from catering to venue
        "serveEvents": serve_events,
        "businessName": venue_data.get('name', ''),
        "slug": slug,
        "businessStartYear": business_start_year,
        "businessDescription": venue_data.get('description', '').replace('\n', ' ')[:500],  # Limit description
        "businessEmail": f"info@{slug.replace('-', '')}.com",  # Generate email
        "businessPhone": venue_data.get('phoneNumber', ''),
        "businessWebsite": f"https://www.{slug.replace('-', '')}.com",  # Generate website
        "contactPerson": "Events Manager",  # Default contact person
        "line_one": line_one,
        "line_two": "",
        "city": city,
        "state": state,
        "zip": zip_code,
        "country": "US",
        "serviceRadius": random.randint(25, 100),  # Random service radius
        "leadTime": random.randint(7, 30),  # Random lead time in days
        "responseTime": 24,  # Default response time in hours
        "serviceLanguages": ["en"],
        "accessibility": "wheelchair_accessible" if any("handicap" in faq.get('question', '').lower() or 
                                                       "accessible" in faq.get('answer', '').lower() 
                                                       for faq in venue_data.get('faqs', [])) else "not_specified",
        "lat": lat,
        "lng": lng,
        "lic": f"VEN-{business_start_year}-{state}-{random.randint(1000, 9999)}",  # Generate license
        "bl": f"BL-{state}-{business_start_year}-{random.randint(1000, 9999)}",  # Generate business license
        "rating": rating,
        "reviewCount": max(review_count, random.randint(50, 200)),  # Ensure minimum reviews
        "budgetMin": f"${budget_min:,}",
        "budgetMax": f"${budget_max:,}"
    }
    
    return mongo_structure

def process_venues(json_file_path, num_venues):
    """
    Process venues from JSON file and convert to MongoDB structure
    
    Args:
        json_file_path (str): Path to the JSON file containing venue data
        num_venues (int): Number of venues to process
    
    Returns:
        list: List of MongoDB documents
    """
    try:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            venues_data = json.load(file)
        
        # Handle both single venue and array of venues
        if isinstance(venues_data, dict):
            venues_data = [venues_data]
        
        processed_venues = []
        
        for i, venue in enumerate(venues_data):
            if i >= num_venues:
                break
                
            try:
                mongo_doc = convert_venue_to_mongo(venue)
                processed_venues.append(mongo_doc)
                print(f"Processed venue {i+1}: {venue.get('name', 'Unknown')}")
            except Exception as e:
                print(f"Error processing venue {i+1}: {str(e)}")
                continue
        
        return processed_venues
        
    except FileNotFoundError:
        print(f"Error: File {json_file_path} not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in file {json_file_path}: {str(e)}")
        return []
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

def save_to_file(mongo_documents, output_file_path):
    """Save MongoDB documents to JSON file"""
    try:
        with open(output_file_path, 'w', encoding='utf-8') as file:
            json.dump(mongo_documents, file, indent=2, ensure_ascii=False)
        print(f"Successfully saved {len(mongo_documents)} documents to {output_file_path}")
    except Exception as e:
        print(f"Error saving to file: {str(e)}")

# Example usage
if __name__ == "__main__":
    # Configuration
    INPUT_FILE = "scripts/input.json"  # Path to your input JSON file
    OUTPUT_FILE = "mongo_venues.json"  # Output file path
    NUM_VENUES = 700  # Number of venues to process
    
    print(f"Processing {NUM_VENUES} venues from {INPUT_FILE}...")
    
    # Process venues
    mongo_docs = process_venues(INPUT_FILE, NUM_VENUES)
    
    if mongo_docs:
        # Save to file
        save_to_file(mongo_docs, OUTPUT_FILE)
        
        # Display first document as example
        print("\nExample of converted document:")
        print(json.dumps(mongo_docs[0], indent=2))
        
        print(f"\nConversion completed! {len(mongo_docs)} venues processed.")
    else:
        print("No venues were processed successfully.")