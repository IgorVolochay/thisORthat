import argparse
import sys
import json
from datetime import datetime
from pathlib import Path

#sys.path.append('..')
from mongo_worker import MongoWorker
from schemas.base_schemas import Card


def create_cards(num_cards=10, author_id=1):
    cards_list = []
    for card_id in range(1, num_cards + 1):
        print(f"Creating Card {card_id}")
        card = Card(
            card_id=card_id,
            choice_A=input("Choice A: "),
            choice_B=input("Choice B: "),
            author_id=author_id,
            creation_date=datetime.now().isoformat(),
            moderation_date=datetime.now().isoformat(),
            active_status=True
        )
        cards_list.append(card)
    return cards_list

def read_json(json_file):
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return [Card(**card) for card in data]
    except Exception as e:
        print(f"Error reading JSON file: {e}")
        return []

def write_json(cards_list, json_file):
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump([card.model_dump() for card in cards_list], f, ensure_ascii=False, indent=4)
        print(f"Successfully saved {len(cards_list)} cards to {json_file}")
    except Exception as e:
        print(f"Error writing to JSON file: {e}")

def add_cards_to_mongodb(cards_list):
    mongo = MongoWorker()
    for card in cards_list:
        mongo.add_card_by_base_model(card)
    print(f"Successfully added {len(cards_list)} cards to MongoDB")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', '--action', type=int, required=True, choices=[0, 1, 2],
                        help="0 - Manual input & save to MongoDB, 1 - Manual input & save to JSON, 2 - Read JSON & save to MongoDB")
    parser.add_argument('-f', '--file', type=str, default="cards.json", help="JSON file name for reading/writing")
    parser.add_argument('-n', '--num', type=int, default=10, help="Number of cards to create")
    parser.add_argument('-u', '--user', type=int, default=1, help="Author ID")
    
    args = parser.parse_args()
    
    if args.action == 0:
        cards = create_cards(args.num, args.user)
        add_cards_to_mongodb(cards)
    elif args.action == 1:
        cards = create_cards(args.num, args.user)
        write_json(cards, args.file)
    elif args.action == 2:
        cards = read_json(args.file)
        if cards:
            add_cards_to_mongodb(cards)
        else:
            print("No valid cards found in JSON file.")
