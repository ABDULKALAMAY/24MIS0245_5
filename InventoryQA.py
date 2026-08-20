"""
QA Test Suite for Inventory and Supply Chain Management System
Comprehensive testing of inventory operations and edge cases
"""

import unittest
import sys
from io import StringIO
from InventoryManagement import InventoryManagement, ReorderStatus
from concurrent.futures import ThreadPoolExecutor
import threading


class TestInventoryManagement(unittest.TestCase):
    """Test suite for Inventory Management System"""

    def setUp(self):
        """Initialize inventory system for each test"""
        self.inventory = InventoryManagement()
        
        # Set up test data
        self.inventory.add_product('A', 'Laptop', 100, 1200.00)
        self.inventory.add_product('B', 'Laptop', 50, 1200.00)
        self.inventory.add_product('C', 'Laptop', 30, 1200.00)
        
        self.inventory.add_product('A', 'Mouse', 200, 25.00)
        self.inventory.add_product('B', 'Keyboard', 150, 75.00)
        self.inventory.add_product('C', 'Monitor', 80, 350.00)

    # ==================== Stock Availability Tests ====================

    def test_stock_availability_sufficient(self):
        """Test: Stock availability when inventory is sufficient"""
        stock = self.inventory.check_stock('A', 'Laptop')
        self.assertEqual(stock, 100, "Should return correct stock quantity")

    def test_stock_availability_zero(self):
        """Test: Stock availability when inventory is zero"""
        self.inventory.remove_product('A', 'Mouse', 200)
        stock = self.inventory.check_stock('A', 'Mouse')
        self.assertEqual(stock, 0, "Should return 0 when stock is depleted")

    def test_stock_availability_product_not_found(self):
        """Test: Stock availability for non-existent product"""
        stock = self.inventory.check_stock('A', 'NonExistent')
        self.assertEqual(stock, -1, "Should return -1 for non-existent product")

    def test_stock_availability_warehouse_not_found(self):
        """Test: Stock availability for invalid warehouse"""
        stock = self.inventory.check_stock('Z', 'Laptop')
        self.assertEqual(stock, -1, "Should return -1 for invalid warehouse")

    # ==================== Insufficient Inventory Tests ====================

    def test_insufficient_inventory_remove(self):
        """Test: Attempt to remove more than available"""
        result = self.inventory.remove_product('A', 'Laptop', 150)
        self.assertFalse(result, "Should fail when removing more than available")
        # Verify stock unchanged
        self.assertEqual(self.inventory.check_stock('A', 'Laptop'), 100)

    def test_insufficient_inventory_fulfill_order(self):
        """Test: Fail to fulfill order with insufficient inventory"""
        result = self.inventory.fulfill_order('Laptop', 200)
        self.assertFalse(result, "Should fail when total inventory insufficient")

    def test_insufficient_inventory_transfer(self):
        """Test: Attempt to transfer more than available"""
        result = self.inventory.transfer_stock('A', 'B', 'Laptop', 150)
        self.assertFalse(result, "Should fail when transferring more than available")

    def test_insufficient_inventory_single_warehouse(self):
        """Test: Insufficient stock in requested warehouse"""
        result = self.inventory.remove_product('C', 'Laptop', 50)
        self.assertFalse(result, "Should fail with only 30 units available")

    # ==================== Warehouse Transfer Tests ====================

    def test_transfer_stock_valid(self):
        """Test: Valid stock transfer between warehouses"""
        result = self.inventory.transfer_stock('A', 'B', 'Laptop', 20)
        self.assertTrue(result, "Transfer should succeed")
        self.assertEqual(self.inventory.check_stock('A', 'Laptop'), 80)
        self.assertEqual(self.inventory.check_stock('B', 'Laptop'), 70)

    def test_transfer_stock_same_warehouse(self):
        """Test: Prevent transfer to same warehouse"""
        result = self.inventory.transfer_stock('A', 'A', 'Laptop', 10)
        self.assertFalse(result, "Should prevent transfer to same warehouse")

    def test_transfer_stock_new_product(self):
        """Test: Transfer product not yet in destination warehouse"""
        result = self.inventory.transfer_stock('A', 'B', 'Mouse', 50)
        self.assertTrue(result, "Transfer should create product in destination")
        self.assertEqual(self.inventory.check_stock('B', 'Mouse'), 50)

    def test_transfer_stock_multiple_times(self):
        """Test: Multiple transfers of same product"""
        self.inventory.transfer_stock('A', 'B', 'Laptop', 10)
        self.inventory.transfer_stock('B', 'C', 'Laptop', 15)
        
        self.assertEqual(self.inventory.check_stock('A', 'Laptop'), 90)
        self.assertEqual(self.inventory.check_stock('B', 'Laptop'), 45)
        self.assertEqual(self.inventory.check_stock('C', 'Laptop'), 45)

    def test_transfer_invalid_warehouse(self):
        """Test: Transfer with invalid warehouse ID"""
        result = self.inventory.transfer_stock('A', 'Z', 'Laptop', 10)
        self.assertFalse(result, "Should fail with invalid warehouse")

    # ==================== Concurrent Orders Tests ====================

    def test_concurrent_orders_same_product(self):
        """Test: Multiple concurrent orders of same product"""
        def place_order():
            return self.inventory.fulfill_order('Mouse', 10)
        
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = list(executor.map(lambda _: place_order(), range(5)))
        
        # At least some orders should succeed (50 units available, 5 orders of 10)
        successful = sum(1 for r in results if r)
        self.assertEqual(successful, 5, "All 5 orders should succeed (50 units available)")
        self.assertEqual(self.inventory.check_stock('A', 'Mouse'), 150)

    def test_concurrent_orders_different_products(self):
        """Test: Concurrent orders of different products"""
        def order_laptop():
            return self.inventory.fulfill_order('Laptop', 5)
        
        def order_keyboard():
            return self.inventory.fulfill_order('Keyboard', 10)
        
        with ThreadPoolExecutor(max_workers=4) as executor:
            future1 = executor.submit(order_laptop)
            future2 = executor.submit(order_keyboard)
            
            result1 = future1.result()
            result2 = future2.result()
        
        self.assertTrue(result1, "Laptop order should succeed")
        self.assertTrue(result2, "Keyboard order should succeed")

    def test_concurrent_transfer_and_removal(self):
        """Test: Concurrent transfer and removal operations"""
        def transfer():
            return self.inventory.transfer_stock('A', 'B', 'Laptop', 5)
        
        def remove():
            return self.inventory.remove_product('A', 'Laptop', 5)
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            results = [
                executor.submit(transfer).result(),
                executor.submit(remove).result(),
                executor.submit(transfer).result()
            ]
        
        # All operations should succeed
        self.assertTrue(all(results), "All concurrent operations should succeed")

    # ==================== Reorder Threshold Tests ====================

    def test_reorder_threshold_trigger(self):
        """Test: Reorder triggered when stock falls below threshold"""
        self.inventory.set_reorder_threshold(100)
        
        # Remove product to trigger reorder
        self.inventory.remove_product('A', 'Laptop', 5)  # 95 left, below 100
        
        pending = self.inventory.get_reorder_queue()
        self.assertEqual(len(pending), 1, "Reorder should be triggered")
        self.assertEqual(pending[0]['product'], 'Laptop')

    def test_reorder_no_trigger_above_threshold(self):
        """Test: No reorder when stock remains above threshold"""
        self.inventory.set_reorder_threshold(50)
        
        self.inventory.remove_product('A', 'Laptop', 10)  # 90 left, above 50
        
        pending = self.inventory.get_reorder_queue()
        self.assertEqual(len(pending), 0, "No reorder should trigger")

    def test_reorder_process(self):
        """Test: Process pending reorder"""
        self.inventory.set_reorder_threshold(100)
        self.inventory.remove_product('A', 'Laptop', 5)
        
        pending_before = len(self.inventory.get_reorder_queue())
        self.assertEqual(pending_before, 1)
        
        # Process reorder
        result = self.inventory.process_reorder('Laptop')
        self.assertTrue(result, "Reorder should process successfully")
        
        # Check status changed
        all_reorders = self.inventory.reorder_queue
        laptop_reorder = [r for r in all_reorders if r['product'] == 'Laptop'][0]
        self.assertEqual(laptop_reorder['status'], ReorderStatus.COMPLETED.value)

    def test_reorder_queue_multiple_products(self):
        """Test: Reorder queue with multiple products"""
        self.inventory.set_reorder_threshold(150)
        
        self.inventory.remove_product('A', 'Laptop', 10)    # Below 150
        self.inventory.remove_product('B', 'Keyboard', 30)   # Below 150
        
        pending = self.inventory.get_reorder_queue()
        self.assertEqual(len(pending), 2, "Two reorders should be pending")

    # ==================== Invalid Product Tests ====================

    def test_invalid_product_remove(self):
        """Test: Remove non-existent product"""
        result = self.inventory.remove_product('A', 'InvalidProduct', 10)
        self.assertFalse(result, "Should fail removing non-existent product")

    def test_invalid_product_transfer(self):
        """Test: Transfer non-existent product"""
        result = self.inventory.transfer_stock('A', 'B', 'InvalidProduct', 10)
        self.assertFalse(result, "Should fail transferring non-existent product")

    def test_invalid_product_check_stock(self):
        """Test: Check stock of non-existent product"""
        stock = self.inventory.check_stock('A', 'InvalidProduct')
        self.assertEqual(stock, -1, "Should return -1 for invalid product")

    def test_invalid_product_fulfill_order(self):
        """Test: Fulfill order for non-existent product"""
        result = self.inventory.fulfill_order('InvalidProduct', 10)
        self.assertFalse(result, "Should fail for non-existent product")

    # ==================== Negative Inventory Tests ====================

    def test_negative_inventory_add_product(self):
        """Test: Prevent adding negative quantity"""
        result = self.inventory.add_product('A', 'TestProduct', -10)
        self.assertFalse(result, "Should reject negative quantity on add")

    def test_negative_inventory_remove_product(self):
        """Test: Prevent removing negative quantity"""
        result = self.inventory.remove_product('A', 'Laptop', -10)
        self.assertFalse(result, "Should reject negative quantity on remove")

    def test_negative_inventory_transfer(self):
        """Test: Prevent transferring negative quantity"""
        result = self.inventory.transfer_stock('A', 'B', 'Laptop', -10)
        self.assertFalse(result, "Should reject negative quantity on transfer")

    def test_negative_inventory_fulfill_order(self):
        """Test: Prevent fulfilling negative quantity order"""
        result = self.inventory.fulfill_order('Laptop', -10)
        self.assertFalse(result, "Should reject negative quantity on order")

    def test_inventory_never_negative(self):
        """Test: Verify inventory can never become negative"""
        self.inventory.remove_product('A', 'Laptop', 100)
        stock = self.inventory.check_stock('A', 'Laptop')
        self.assertEqual(stock, 0, "Stock should be 0, never negative")
        self.assertGreaterEqual(stock, 0, "Stock should never be negative")

    # ==================== Multiple Warehouses Tests ====================

    def test_warehouse_selection_automatic(self):
        """Test: Automatic warehouse selection for order fulfillment"""
        warehouse = self.inventory.find_warehouse_for_order('Laptop', 30)
        self.assertIsNotNone(warehouse, "Should find warehouse")
        self.assertIn(warehouse, ['A', 'B', 'C'], "Should select valid warehouse")

    def test_warehouse_selection_insufficient_any(self):
        """Test: No warehouse available for large order"""
        warehouse = self.inventory.find_warehouse_for_order('Laptop', 200)
        self.assertIsNone(warehouse, "Should return None when no warehouse has enough")

    def test_warehouse_selection_optimal(self):
        """Test: Warehouse selection chooses optimal option"""
        # A: 100, B: 50, C: 30
        warehouse = self.inventory.find_warehouse_for_order('Laptop', 25)
        # Should select C (30 units, least excess)
        self.assertEqual(warehouse, 'C', "Should select warehouse with least excess stock")

    def test_multiple_warehouses_inventory_query(self):
        """Test: Query inventory across multiple warehouses"""
        total = self.inventory.get_total_stock('Laptop')
        expected = 100 + 50 + 30  # A + B + C
        self.assertEqual(total, expected, "Should return total across all warehouses")

    def test_warehouse_not_found(self):
        """Test: Operations with non-existent warehouse"""
        result = self.inventory.add_product('Z', 'Product', 10)
        self.assertFalse(result, "Should fail with invalid warehouse")

    def test_low_stock_across_warehouses(self):
        """Test: Low stock detection across multiple warehouses"""
        self.inventory.set_reorder_threshold(150)
        
        self.inventory.remove_product('A', 'Laptop', 10)  # 90, below 150
        self.inventory.remove_product('B', 'Laptop', 20)  # 30, below 150
        # C already has 30 Laptop units from setUp, also below 150
        
        low_stock = self.inventory.get_low_stock_products()
        laptop_low = [item for item in low_stock if item[1] == 'Laptop']
        self.assertEqual(len(laptop_low), 3, "Should detect low stock in all 3 warehouses")

    # ==================== Integration Tests ====================

    def test_full_order_fulfillment_workflow(self):
        """Test: Complete workflow from order to fulfillment"""
        # Find warehouse
        warehouse = self.inventory.find_warehouse_for_order('Laptop', 20)
        self.assertIsNotNone(warehouse)
        
        # Fulfill order
        result = self.inventory.fulfill_order('Laptop', 20)
        self.assertTrue(result, "Order should be fulfilled")
        
        # Verify stock updated
        total = self.inventory.get_total_stock('Laptop')
        self.assertEqual(total, 160, "Total should be reduced by 20")

    def test_supplier_management(self):
        """Test: Supplier registration and lookup"""
        self.inventory.add_supplier('TechCorp', ['Laptop', 'Mouse'], 2)
        
        suppliers = self.inventory.get_suppliers_for_product('Laptop')
        self.assertIn('TechCorp', suppliers, "Should find supplier for product")
        
        keyboard_suppliers = self.inventory.get_suppliers_for_product('Keyboard')
        self.assertNotIn('TechCorp', keyboard_suppliers, "Should not find supplier for other products")

    def test_report_generation(self):
        """Test: Inventory report generation"""
        report = self.inventory.generate_inventory_report()
        self.assertIn('Warehouse A', report)
        self.assertIn('Warehouse B', report)
        self.assertIn('Warehouse C', report)
        self.assertIn('Laptop', report)

    def test_warehouse_inventory_snapshot(self):
        """Test: Get complete warehouse inventory"""
        inventory_a = self.inventory.get_warehouse_inventory('A')
        self.assertIn('products', inventory_a)
        self.assertIn('Laptop', inventory_a['products'])
        self.assertEqual(inventory_a['products']['Laptop']['quantity'], 100)


class TestInventoryEdgeCases(unittest.TestCase):
    """Edge case tests for inventory system"""

    def setUp(self):
        """Initialize inventory for edge case tests"""
        self.inventory = InventoryManagement()

    def test_add_same_product_multiple_times(self):
        """Test: Adding same product multiple times updates quantity"""
        self.inventory.add_product('A', 'Laptop', 50)
        self.inventory.add_product('A', 'Laptop', 30)
        
        stock = self.inventory.check_stock('A', 'Laptop')
        self.assertEqual(stock, 80, "Should accumulate quantities")

    def test_empty_warehouse_operations(self):
        """Test: Operations on empty warehouse"""
        stock = self.inventory.check_stock('A', 'Laptop')
        self.assertEqual(stock, -1, "Should return -1 for empty warehouse")

    def test_transfer_entire_stock(self):
        """Test: Transfer entire stock of a product"""
        self.inventory.add_product('A', 'Product', 50)
        result = self.inventory.transfer_stock('A', 'B', 'Product', 50)
        
        self.assertTrue(result, "Should allow transferring entire stock")
        self.assertEqual(self.inventory.check_stock('A', 'Product'), 0)
        self.assertEqual(self.inventory.check_stock('B', 'Product'), 50)

    def test_zero_quantity_operations(self):
        """Test: Operations with zero quantity"""
        self.inventory.add_product('A', 'Product', 100)
        result = self.inventory.remove_product('A', 'Product', 0)
        
        # Should succeed but not change quantity
        self.assertEqual(self.inventory.check_stock('A', 'Product'), 100)

    def test_large_quantity_handling(self):
        """Test: Handle large quantities"""
        result = self.inventory.add_product('A', 'Product', 1000000)
        self.assertTrue(result, "Should handle large quantities")
        
        stock = self.inventory.check_stock('A', 'Product')
        self.assertEqual(stock, 1000000, "Should store large quantities correctly")


def run_tests():
    """Run all tests and generate report"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestInventoryManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestInventoryEdgeCases))
    
    # Run with verbosity
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)
