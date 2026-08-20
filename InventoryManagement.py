"""
Inventory and Supply Chain Management System
Manages inventory across multiple warehouses with automated order fulfillment
"""

from datetime import datetime
from typing import Dict, List, Tuple, Optional
from enum import Enum
import threading


class ReorderStatus(Enum):
    """Status of reorder operations"""
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class InventoryManagement:
    """
    Inventory Management System for multiple warehouses
    Handles product management, stock transfers, and reordering
    """

    def __init__(self):
        """Initialize inventory system with three warehouses"""
        self.warehouses = {
            'A': {'products': {}, 'capacity': 1000, 'location': 'North'},
            'B': {'products': {}, 'capacity': 1500, 'location': 'Central'},
            'C': {'products': {}, 'capacity': 800, 'location': 'South'}
        }
        self.suppliers = {}
        self.reorder_queue = []
        self.low_stock_threshold = 50
        self.lock = threading.RLock()  # Reentrant lock for concurrent order handling

    # ==================== Product Management ====================

    def add_product(self, warehouse_id: str, product_name: str, quantity: int, 
                   price: float = 0.0) -> bool:
        """
        Add product to warehouse inventory
        
        Args:
            warehouse_id: Warehouse identifier (A, B, C)
            product_name: Name of the product
            quantity: Quantity to add
            price: Unit price of product
            
        Returns:
            True if successful, False otherwise
        """
        if warehouse_id not in self.warehouses:
            print(f"Error: Warehouse {warehouse_id} does not exist")
            return False

        if quantity < 0:
            print(f"Error: Negative quantity {quantity} not allowed")
            return False

        with self.lock:
            warehouse = self.warehouses[warehouse_id]
            
            if product_name in warehouse['products']:
                warehouse['products'][product_name]['quantity'] += quantity
                print(f"Updated {product_name} in Warehouse {warehouse_id}: +{quantity}")
            else:
                warehouse['products'][product_name] = {
                    'quantity': quantity,
                    'price': price,
                    'added_date': datetime.now(),
                    'reorder_quantity': 100
                }
                print(f"Added {product_name} to Warehouse {warehouse_id}: {quantity} units")
            
            return True

    def remove_product(self, warehouse_id: str, product_name: str, quantity: int) -> bool:
        """
        Remove product from warehouse inventory
        
        Args:
            warehouse_id: Warehouse identifier
            product_name: Name of the product
            quantity: Quantity to remove
            
        Returns:
            True if successful, False otherwise
        """
        if warehouse_id not in self.warehouses:
            print(f"Error: Warehouse {warehouse_id} does not exist")
            return False

        if quantity < 0:
            print(f"Error: Negative quantity {quantity} not allowed")
            return False

        with self.lock:
            warehouse = self.warehouses[warehouse_id]
            
            if product_name not in warehouse['products']:
                print(f"Error: {product_name} not found in Warehouse {warehouse_id}")
                return False

            current_qty = warehouse['products'][product_name]['quantity']
            
            if current_qty < quantity:
                print(f"Error: Insufficient inventory. Available: {current_qty}, Requested: {quantity}")
                return False

            warehouse['products'][product_name]['quantity'] -= quantity
            print(f"Removed {quantity} units of {product_name} from Warehouse {warehouse_id}")
            
            # Check if low stock
            if warehouse['products'][product_name]['quantity'] <= self.low_stock_threshold:
                self._trigger_reorder(warehouse_id, product_name)
            
            return True

    # ==================== Stock Transfer ====================

    def transfer_stock(self, from_warehouse: str, to_warehouse: str, 
                      product_name: str, quantity: int) -> bool:
        """
        Transfer stock between warehouses
        
        Args:
            from_warehouse: Source warehouse
            to_warehouse: Destination warehouse
            product_name: Product to transfer
            quantity: Quantity to transfer
            
        Returns:
            True if successful, False otherwise
        """
        if from_warehouse not in self.warehouses or to_warehouse not in self.warehouses:
            print("Error: Invalid warehouse identifiers")
            return False

        if quantity < 0:
            print(f"Error: Negative quantity {quantity} not allowed")
            return False

        if from_warehouse == to_warehouse:
            print("Error: Source and destination warehouses cannot be the same")
            return False

        with self.lock:
            from_wh = self.warehouses[from_warehouse]
            to_wh = self.warehouses[to_warehouse]

            # Validate source has product
            if product_name not in from_wh['products']:
                print(f"Error: {product_name} not found in Warehouse {from_warehouse}")
                return False

            if from_wh['products'][product_name]['quantity'] < quantity:
                print(f"Error: Insufficient stock in Warehouse {from_warehouse}")
                return False

            # Update source
            from_wh['products'][product_name]['quantity'] -= quantity

            # Update destination
            if product_name in to_wh['products']:
                to_wh['products'][product_name]['quantity'] += quantity
            else:
                to_wh['products'][product_name] = {
                    'quantity': quantity,
                    'price': from_wh['products'][product_name]['price'],
                    'added_date': datetime.now(),
                    'reorder_quantity': 100
                }

            print(f"Transferred {quantity} units of {product_name} from Warehouse {from_warehouse} to {to_warehouse}")
            return True

    # ==================== Reorder Management ====================

    def _trigger_reorder(self, warehouse_id: str, product_name: str):
        """
        Trigger reorder when stock falls below threshold
        
        Args:
            warehouse_id: Warehouse requiring restock
            product_name: Product to reorder
        """
        reorder_qty = self.warehouses[warehouse_id]['products'][product_name]['reorder_quantity']
        print(f"[!] Low stock alert for {product_name} in Warehouse {warehouse_id}. Reordering {reorder_qty} units...")
        
        reorder_item = {
            'product': product_name,
            'warehouse': warehouse_id,
            'quantity': reorder_qty,
            'status': ReorderStatus.PENDING.value,
            'timestamp': datetime.now()
        }
        self.reorder_queue.append(reorder_item)

    def process_reorder(self, product_name: str) -> bool:
        """
        Process pending reorder for a product
        
        Args:
            product_name: Product to reorder
            
        Returns:
            True if reorder processed successfully
        """
        with self.lock:
            for reorder in self.reorder_queue:
                if reorder['product'] == product_name and reorder['status'] == ReorderStatus.PENDING.value:
                    warehouse_id = reorder['warehouse']
                    quantity = reorder['quantity']
                    
                    if self.add_product(warehouse_id, product_name, quantity):
                        reorder['status'] = ReorderStatus.COMPLETED.value
                        print(f"[OK] Reorder completed for {product_name} in Warehouse {warehouse_id}")
                        return True
        
        return False

    def set_reorder_threshold(self, threshold: int) -> None:
        """Set global low-stock reorder threshold"""
        if threshold < 0:
            print("Error: Threshold cannot be negative")
            return
        self.low_stock_threshold = threshold
        print(f"Reorder threshold set to {threshold} units")

    def get_reorder_queue(self) -> List[Dict]:
        """Get all pending reorders"""
        return [r for r in self.reorder_queue if r['status'] == ReorderStatus.PENDING.value]

    # ==================== Supplier Management ====================

    def add_supplier(self, supplier_name: str, products: List[str], lead_time_days: int) -> bool:
        """
        Register a supplier
        
        Args:
            supplier_name: Name of supplier
            products: List of products supplied
            lead_time_days: Delivery lead time
            
        Returns:
            True if successful
        """
        if supplier_name in self.suppliers:
            print(f"Warning: Supplier {supplier_name} already exists")
            return False

        self.suppliers[supplier_name] = {
            'products': products,
            'lead_time': lead_time_days,
            'registered_date': datetime.now()
        }
        print(f"Supplier {supplier_name} registered for products: {', '.join(products)}")
        return True

    def get_suppliers_for_product(self, product_name: str) -> List[str]:
        """Get all suppliers for a specific product"""
        return [s for s, data in self.suppliers.items() if product_name in data['products']]

    # ==================== Warehouse Selection & Order Fulfillment ====================

    def find_warehouse_for_order(self, product_name: str, quantity: int) -> Optional[str]:
        """
        Automatically identify warehouse for order fulfillment
        Priority: Warehouse with stock, then closest to optimal capacity
        
        Args:
            product_name: Product to order
            quantity: Required quantity
            
        Returns:
            Warehouse ID (A, B, C) or None if insufficient stock
        """
        with self.lock:
            available_warehouses = []
            
            for wh_id, wh_data in self.warehouses.items():
                if product_name in wh_data['products']:
                    stock = wh_data['products'][product_name]['quantity']
                    if stock >= quantity:
                        available_warehouses.append((wh_id, stock))
            
            if not available_warehouses:
                print(f"Error: Insufficient inventory for {product_name} (required: {quantity})")
                return None
            
            # Select warehouse with least excess stock (most efficient)
            best_warehouse = min(available_warehouses, key=lambda x: x[1])[0]
            print(f"[OK] Order fulfillment: Warehouse {best_warehouse} selected for {product_name}")
            return best_warehouse

    def fulfill_order(self, product_name: str, quantity: int) -> bool:
        """
        Fulfill an order from the best available warehouse
        
        Args:
            product_name: Product to order
            quantity: Quantity required
            
        Returns:
            True if order fulfilled successfully
        """
        warehouse = self.find_warehouse_for_order(product_name, quantity)
        if warehouse:
            return self.remove_product(warehouse, product_name, quantity)
        return False

    # ==================== Inventory Query ====================

    def check_stock(self, warehouse_id: str, product_name: str) -> int:
        """
        Check available stock in a warehouse
        
        Args:
            warehouse_id: Warehouse to check
            product_name: Product name
            
        Returns:
            Available quantity or -1 if not found
        """
        if warehouse_id not in self.warehouses:
            return -1
        
        if product_name not in self.warehouses[warehouse_id]['products']:
            return -1
        
        return self.warehouses[warehouse_id]['products'][product_name]['quantity']

    def get_warehouse_inventory(self, warehouse_id: str) -> Dict:
        """Get complete inventory of a warehouse"""
        if warehouse_id not in self.warehouses:
            return {}
        return self.warehouses[warehouse_id].copy()

    def get_total_stock(self, product_name: str) -> int:
        """Get total stock across all warehouses"""
        total = 0
        for warehouse in self.warehouses.values():
            if product_name in warehouse['products']:
                total += warehouse['products'][product_name]['quantity']
        return total

    def get_low_stock_products(self) -> List[Tuple[str, str, int]]:
        """
        Get all products below reorder threshold
        
        Returns:
            List of (warehouse_id, product_name, current_stock)
        """
        low_stock = []
        for wh_id, warehouse in self.warehouses.items():
            for product, data in warehouse['products'].items():
                if data['quantity'] <= self.low_stock_threshold:
                    low_stock.append((wh_id, product, data['quantity']))
        return low_stock

    # ==================== Report Generation ====================

    def generate_inventory_report(self) -> str:
        """Generate comprehensive inventory report"""
        report = "=" * 70 + "\n"
        report += "INVENTORY MANAGEMENT SYSTEM - COMPREHENSIVE REPORT\n"
        report += "=" * 70 + "\n\n"

        for wh_id, warehouse in self.warehouses.items():
            report += f"Warehouse {wh_id} ({warehouse['location']})\n"
            report += f"Capacity: {warehouse['capacity']} units\n"
            report += "-" * 70 + "\n"
            
            if warehouse['products']:
                report += f"{'Product':<20} {'Quantity':<12} {'Status':<20}\n"
                report += "-" * 70 + "\n"
                
                for product, data in warehouse['products'].items():
                    status = "LOW STOCK" if data['quantity'] <= self.low_stock_threshold else "OK"
                    report += f"{product:<20} {data['quantity']:<12} {status:<20}\n"
            else:
                report += "No products in inventory\n"
            
            report += "\n"

        # Low stock summary
        low_stock = self.get_low_stock_products()
        if low_stock:
            report += "[!] LOW STOCK ALERT\n"
            report += "-" * 70 + "\n"
            for wh_id, product, qty in low_stock:
                report += f"Warehouse {wh_id}: {product} - {qty} units\n"

        return report


if __name__ == "__main__":
    # Example usage
    inventory = InventoryManagement()
    
    # Add products to warehouses
    inventory.add_product('A', 'Laptop', 150, 1200.00)
    inventory.add_product('A', 'Mouse', 300, 25.00)
    inventory.add_product('B', 'Keyboard', 200, 75.00)
    inventory.add_product('C', 'Monitor', 100, 350.00)
    
    # Add suppliers
    inventory.add_supplier('TechSupply Co', ['Laptop', 'Mouse', 'Keyboard'], 3)
    inventory.add_supplier('DisplayWorld', ['Monitor'], 2)
    
    # Transfer stock
    inventory.transfer_stock('A', 'B', 'Mouse', 50)
    
    # Fulfill orders
    inventory.fulfill_order('Laptop', 30)
    
    # Generate report
    print(inventory.generate_inventory_report())
