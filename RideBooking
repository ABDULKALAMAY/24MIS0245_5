from datetime import datetime
from typing import Dict, Tuple, Optional

class RideBooking:
    """Ride-Sharing Fare and Driver Allocation System"""
    
    # Vehicle type details: (base_fare, per_km_rate, passenger_limit)
    VEHICLE_TYPES = {
        "Bike": {"base_fare": 50, "per_km_rate": 8, "passenger_limit": 1},
        "Sedan": {"base_fare": 100, "per_km_rate": 15, "passenger_limit": 4},
        "SUV": {"base_fare": 150, "per_km_rate": 20, "passenger_limit": 6},
        "Premium": {"base_fare": 200, "per_km_rate": 25, "passenger_limit": 4}
    }
    
    # Peak hours (18:00-23:59 and 7:00-9:59)
    PEAK_HOURS = [(7, 10), (18, 24)]
    
    # Night hours (0:00-6:59)
    NIGHT_HOURS = [(0, 7)]
    
    # Promotional discount percentages
    MAX_DISCOUNT_PERCENTAGE = 20
    
    def __init__(self):
        self.drivers = {
            1: {"name": "Driver A", "available": True, "vehicle": "Sedan"},
            2: {"name": "Driver B", "available": True, "vehicle": "SUV"},
            3: {"name": "Driver C", "available": False, "vehicle": "Bike"},
            4: {"name": "Driver D", "available": True, "vehicle": "Premium"},
            5: {"name": "Driver E", "available": True, "vehicle": "Sedan"},
        }
    
    def validate_booking(self, customer_id: str, pickup: str, drop: str, 
                        distance: float, passengers: int, vehicle_type: str,
                        booking_time: str) -> Tuple[bool, str]:
        """Validate booking input parameters"""
        
        # Validate customer ID
        if not customer_id or not isinstance(customer_id, str):
            return False, "Invalid customer ID"
        
        # Validate locations
        if not pickup or not drop:
            return False, "Pickup and drop locations cannot be empty"
        
        if pickup == drop:
            return False, "Pickup and drop locations cannot be the same"
        
        # Validate distance
        if distance <= 0:
            return False, "Distance must be greater than zero"
        
        if distance > 500:
            return False, "Distance exceeds maximum limit (500 km)"
        
        # Validate passenger count
        if passengers <= 0:
            return False, "Passenger count must be at least 1"
        
        if passengers > 6:
            return False, "Passenger count exceeds maximum limit (6)"
        
        # Validate vehicle type
        if vehicle_type not in self.VEHICLE_TYPES:
            return False, f"Invalid vehicle type. Choose from: {', '.join(self.VEHICLE_TYPES.keys())}"
        
        # Validate passenger limit for vehicle type
        max_passengers = self.VEHICLE_TYPES[vehicle_type]["passenger_limit"]
        if passengers > max_passengers:
            return False, f"Vehicle {vehicle_type} cannot accommodate {passengers} passengers (max: {max_passengers})"
        
        # Validate booking time
        try:
            booking_datetime = datetime.strptime(booking_time, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return False, "Invalid booking time format (use: YYYY-MM-DD HH:MM:SS)"
        
        return True, "Booking validated successfully"
    
    def calculate_base_fare(self, vehicle_type: str) -> float:
        """Calculate base fare for vehicle type"""
        return self.VEHICLE_TYPES[vehicle_type]["base_fare"]
    
    def calculate_distance_fare(self, distance: float, vehicle_type: str) -> float:
        """Calculate distance-based fare"""
        per_km_rate = self.VEHICLE_TYPES[vehicle_type]["per_km_rate"]
        return distance * per_km_rate
    
    def is_peak_hour(self, booking_time: str) -> bool:
        """Check if booking is during peak hours"""
        try:
            booking_datetime = datetime.strptime(booking_time, "%Y-%m-%d %H:%M:%S")
            hour = booking_datetime.hour
            
            for start, end in self.PEAK_HOURS:
                if start <= hour < end:
                    return True
            return False
        except ValueError:
            return False
    
    def is_night_hour(self, booking_time: str) -> bool:
        """Check if booking is during night hours"""
        try:
            booking_datetime = datetime.strptime(booking_time, "%Y-%m-%d %H:%M:%S")
            hour = booking_datetime.hour
            
            for start, end in self.NIGHT_HOURS:
                if start <= hour < end:
                    return True
            return False
        except ValueError:
            return False
    
    def calculate_peak_hour_surcharge(self, base_amount: float, booking_time: str) -> float:
        """Calculate peak-hour surcharge (20% of base fare + distance fare)"""
        if self.is_peak_hour(booking_time):
            return base_amount * 0.20
        return 0.0
    
    def calculate_night_surcharge(self, base_amount: float, booking_time: str) -> float:
        """Calculate night surcharge (25% of base fare + distance fare)"""
        if self.is_night_hour(booking_time):
            return base_amount * 0.25
        return 0.0
    
    def calculate_passenger_surcharge(self, passengers: int, base_amount: float) -> float:
        """Calculate passenger surcharge (5% per additional passenger over 1)"""
        if passengers > 1:
            additional_passengers = passengers - 1
            return base_amount * (0.05 * additional_passengers)
        return 0.0
    
    def calculate_discount(self, base_amount: float, discount_percentage: float) -> float:
        """Calculate promotional discount"""
        if discount_percentage < 0 or discount_percentage > self.MAX_DISCOUNT_PERCENTAGE:
            discount_percentage = 0
        return base_amount * (discount_percentage / 100)
    
    def assign_driver(self, vehicle_type: str) -> Tuple[Optional[int], Optional[str]]:
        """Assign an available driver of the specified vehicle type"""
        for driver_id, driver_info in self.drivers.items():
            if driver_info["available"] and driver_info["vehicle"] == vehicle_type:
                return driver_id, driver_info["name"]
        
        return None, "No available driver for the specified vehicle type"
    
    def book_ride(self, customer_id: str, pickup: str, drop: str, distance: float,
                  passengers: int, vehicle_type: str, booking_time: str,
                  driver_availability: bool = True, discount_percentage: float = 0) -> Dict:
        """Book a ride and calculate fare"""
        
        # Validate booking
        is_valid, validation_message = self.validate_booking(
            customer_id, pickup, drop, distance, passengers, vehicle_type, booking_time
        )
        
        if not is_valid:
            return {
                "success": False,
                "error": validation_message,
                "customer_id": customer_id,
                "booking_time": booking_time
            }
        
        # Check driver availability
        driver_id, driver_name = self.assign_driver(vehicle_type)
        
        if driver_id is None:
            if not driver_availability:
                return {
                    "success": False,
                    "error": driver_name,
                    "customer_id": customer_id,
                    "vehicle_type": vehicle_type
                }
            else:
                return {
                    "success": False,
                    "error": f"No available driver for {vehicle_type}",
                    "customer_id": customer_id,
                    "vehicle_type": vehicle_type
                }
        
        # Calculate fare components
        base_fare = self.calculate_base_fare(vehicle_type)
        distance_fare = self.calculate_distance_fare(distance, vehicle_type)
        base_amount = base_fare + distance_fare
        
        peak_surcharge = self.calculate_peak_hour_surcharge(base_amount, booking_time)
        night_surcharge = self.calculate_night_surcharge(base_amount, booking_time)
        passenger_surcharge = self.calculate_passenger_surcharge(passengers, base_amount)
        
        subtotal = base_amount + peak_surcharge + night_surcharge + passenger_surcharge
        
        discount = self.calculate_discount(subtotal, discount_percentage)
        final_fare = subtotal - discount
        
        return {
            "success": True,
            "customer_id": customer_id,
            "pickup": pickup,
            "drop": drop,
            "distance": distance,
            "passengers": passengers,
            "vehicle_type": vehicle_type,
            "booking_time": booking_time,
            "driver_id": driver_id,
            "driver_name": driver_name,
            "base_fare": base_fare,
            "distance_fare": distance_fare,
            "peak_hour_surcharge": peak_surcharge,
            "night_surcharge": night_surcharge,
            "passenger_surcharge": passenger_surcharge,
            "subtotal": subtotal,
            "discount_percentage": discount_percentage,
            "discount_amount": discount,
            "final_fare": round(final_fare, 2),
            "is_peak_hour": self.is_peak_hour(booking_time),
            "is_night_hour": self.is_night_hour(booking_time)
        }


def main():
    """Main function to demonstrate the ride-sharing system"""
    ride_system = RideBooking()
    
    # Test Case 1: Normal booking
    print("=" * 60)
    print("Test Case 1: Normal Booking")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST001",
        pickup="Downtown",
        drop="Airport",
        distance=25,
        passengers=2,
        vehicle_type="Sedan",
        booking_time="2024-01-15 14:00:00",
        driver_availability=True,
        discount_percentage=0
    )
    print_booking_result(result)
    
    # Test Case 2: Peak-hour booking
    print("\n" + "=" * 60)
    print("Test Case 2: Peak-Hour Booking")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST002",
        pickup="Mall",
        drop="Office",
        distance=15,
        passengers=1,
        vehicle_type="Sedan",
        booking_time="2024-01-15 18:30:00",
        driver_availability=True
    )
    print_booking_result(result)
    
    # Test Case 3: Night booking
    print("\n" + "=" * 60)
    print("Test Case 3: Night Booking")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST003",
        pickup="Home",
        drop="Station",
        distance=10,
        passengers=1,
        vehicle_type="Bike",
        booking_time="2024-01-15 02:00:00"
    )
    print_booking_result(result)
    
    # Test Case 4: Invalid distance
    print("\n" + "=" * 60)
    print("Test Case 4: Invalid Distance (Zero)")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST004",
        pickup="Location A",
        drop="Location B",
        distance=0,
        passengers=2,
        vehicle_type="SUV",
        booking_time="2024-01-15 15:00:00"
    )
    print_booking_result(result)
    
    # Test Case 5: Invalid passenger count
    print("\n" + "=" * 60)
    print("Test Case 5: Invalid Passenger Count (Exceeds Bike Limit)")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST005",
        pickup="Place1",
        drop="Place2",
        distance=5,
        passengers=2,
        vehicle_type="Bike",
        booking_time="2024-01-15 12:00:00"
    )
    print_booking_result(result)
    
    # Test Case 6: Maximum discount
    print("\n" + "=" * 60)
    print("Test Case 6: Maximum Discount Applied")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST006",
        pickup="Market",
        drop="Hotel",
        distance=20,
        passengers=3,
        vehicle_type="SUV",
        booking_time="2024-01-15 16:00:00",
        discount_percentage=20
    )
    print_booking_result(result)
    
    # Test Case 7: Premium vehicle booking
    print("\n" + "=" * 60)
    print("Test Case 7: Premium Vehicle Booking")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST007",
        pickup="VIP Zone",
        drop="Executive Tower",
        distance=30,
        passengers=2,
        vehicle_type="Premium",
        booking_time="2024-01-15 19:00:00",
        discount_percentage=5
    )
    print_booking_result(result)
    
    # Test Case 8: Unavailable driver scenario
    print("\n" + "=" * 60)
    print("Test Case 8: Unavailable Driver")
    print("=" * 60)
    ride_system.drivers[1]["available"] = False
    ride_system.drivers[5]["available"] = False
    result = ride_system.book_ride(
        customer_id="CUST008",
        pickup="Start",
        drop="End",
        distance=10,
        passengers=2,
        vehicle_type="Sedan",
        booking_time="2024-01-15 20:00:00",
        driver_availability=False
    )
    print_booking_result(result)
    ride_system.drivers[1]["available"] = True
    ride_system.drivers[5]["available"] = True
    
    # Test Case 9: Maximum passenger SUV
    print("\n" + "=" * 60)
    print("Test Case 9: Maximum Passengers (SUV)")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST009",
        pickup="Terminal",
        drop="Convention Center",
        distance=18,
        passengers=6,
        vehicle_type="SUV",
        booking_time="2024-01-15 11:00:00"
    )
    print_booking_result(result)
    
    # Test Case 10: Peak hour with multiple passengers
    print("\n" + "=" * 60)
    print("Test Case 10: Peak Hour with Multiple Passengers")
    print("=" * 60)
    result = ride_system.book_ride(
        customer_id="CUST010",
        pickup="Business District",
        drop="Hospital",
        distance=12,
        passengers=4,
        vehicle_type="SUV",
        booking_time="2024-01-15 08:30:00"
    )
    print_booking_result(result)


def print_booking_result(result: Dict):
    """Pretty print booking result"""
    if result["success"]:
        print(f"✓ Booking Successful")
        print(f"  Customer ID: {result['customer_id']}")
        print(f"  Route: {result['pickup']} → {result['drop']}")
        print(f"  Distance: {result['distance']} km")
        print(f"  Passengers: {result['passengers']}")
        print(f"  Vehicle Type: {result['vehicle_type']}")
        print(f"  Driver: {result['driver_name']} (ID: {result['driver_id']})")
        print(f"  Booking Time: {result['booking_time']}")
        print(f"  Peak Hour: {'Yes' if result['is_peak_hour'] else 'No'}")
        print(f"  Night Hour: {'Yes' if result['is_night_hour'] else 'No'}")
        print(f"\n  Fare Breakdown:")
        print(f"    Base Fare: ₹{result['base_fare']:.2f}")
        print(f"    Distance Fare: ₹{result['distance_fare']:.2f}")
        print(f"    Peak Hour Surcharge: ₹{result['peak_hour_surcharge']:.2f}")
        print(f"    Night Surcharge: ₹{result['night_surcharge']:.2f}")
        print(f"    Passenger Surcharge: ₹{result['passenger_surcharge']:.2f}")
        print(f"    Subtotal: ₹{result['subtotal']:.2f}")
        print(f"    Discount ({result['discount_percentage']}%): -₹{result['discount_amount']:.2f}")
        print(f"    FINAL FARE: ₹{result['final_fare']:.2f}")
    else:
        print(f"✗ Booking Failed")
        print(f"  Error: {result['error']}")
        print(f"  Customer ID: {result['customer_id']}")


if __name__ == "__main__":
    main()
