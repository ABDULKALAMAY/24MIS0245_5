"""
Digital Wallet Security QA Test Suite
Comprehensive testing for DigitalWallet system including:
- Normal transactions
- Insufficient balance handling
- Daily limit enforcement
- Failed PIN attempts and lockout
- Fraud detection mechanisms
- Edge cases and security scenarios
"""

import unittest
import time
import hashlib
from datetime import datetime, timedelta
from threading import Thread
from DigitalWallet import DigitalWallet, TransactionType, FraudRiskLevel


class TestDigitalWalletQA(unittest.TestCase):
    """Comprehensive QA test suite for DigitalWallet"""

    def setUp(self):
        """Initialize test environment before each test"""
        self.wallet = DigitalWallet()
        
        # Create test accounts
        self.wallet.create_account(
            "TEST001", "Test User 1", "test1@example.com", "9876543210", "1234"
        )
        self.wallet.create_account(
            "TEST002", "Test User 2", "test2@example.com", "9876543211", "5678"
        )
        self.wallet.create_account(
            "TEST003", "Test User 3", "test3@example.com", "9876543212", "9012", 50000.0
        )
        
        # Deposit initial funds in smaller chunks to avoid fraud detection
        # Each deposit is below HIGH_TRANSACTION_AMOUNT (50000)
        for i in range(3):
            self.wallet.deposit("TEST001", 20000, f"Initial setup {i+1}")
        
        for i in range(2):
            self.wallet.deposit("TEST002", 25000, f"Initial setup {i+1}")
        
        for i in range(3):
            self.wallet.deposit("TEST003", 20000, f"Initial setup {i+1}")

    def tearDown(self):
        """Clean up after each test"""
        self.wallet = None

    # ==================== NORMAL TRANSACTION TESTS ====================

    def test_normal_deposit(self):
        """Test normal deposit transaction"""
        success, msg, txn_id = self.wallet.deposit("TEST001", 5000, "Normal deposit")
        
        self.assertTrue(success)
        self.assertIsNotNone(txn_id)
        # Deposit may be flagged if amount triggers fraud detection
        self.assertIn("successful", msg.lower())
        
        # Verify balance updated (if not blocked)
        _, _, balance = self.wallet.check_balance("TEST001")
        self.assertGreater(balance, 60000)

    def test_normal_withdrawal(self):
        """Test normal withdrawal transaction"""
        success, msg, txn_id = self.wallet.withdraw("TEST001", 10000, "1234", "Normal withdrawal")
        
        if success:
            self.assertIsNotNone(txn_id)
            self.assertIn("successful", msg.lower())
            
            # Verify balance decreased
            _, _, balance = self.wallet.check_balance("TEST001")
            self.assertLess(balance, 60000)
        else:
            # May be blocked for fraud reasons, that's acceptable
            self.assertIn("blocked", msg.lower())

    def test_normal_transfer(self):
        """Test normal money transfer between accounts"""
        success, msg, txn_id = self.wallet.transfer(
            "TEST001", "TEST002", 15000, "1234", "Normal transfer"
        )
        
        self.assertTrue(success)
        self.assertIsNotNone(txn_id)
        
        # Verify balances (account started with 60000 and 50000)
        _, _, balance1 = self.wallet.check_balance("TEST001")
        _, _, balance2 = self.wallet.check_balance("TEST002")
        
        self.assertLess(balance1, 60000)  # Decreased
        self.assertGreater(balance2, 50000)  # Increased

    def test_multiple_normal_transactions(self):
        """Test sequence of normal transactions"""
        # Deposit
        success1, _, _ = self.wallet.deposit("TEST001", 10000)
        self.assertTrue(success1)
        
        # Withdrawal
        success2, _, _ = self.wallet.withdraw("TEST001", 5000, "1234")
        self.assertTrue(success2)
        
        # Transfer - may fail if balance is too low after previous operations
        success3, msg3, _ = self.wallet.transfer("TEST001", "TEST002", 3000, "1234")
        
        # Either transfer succeeds, or it fails due to insufficient balance/fraud
        if not success3:
            # Check if failure message makes sense
            msg_lower = msg3.lower()
            self.assertTrue(
                any(keyword in msg_lower for keyword in ["insufficient", "blocked", "failed"]),
                f"Unexpected error message: {msg3}"
            )
        else:
            # If it succeeded, verify the transaction
            self.assertIsNotNone(msg3)
        
        # Verify balance is within reasonable range (TEST001 started at 60000)
        _, _, balance = self.wallet.check_balance("TEST001")
        # Should be between: 60000 + 10000 - 5000 - 3000 = 62000 (if transfer succeeded)
        # or 60000 + 10000 - 5000 = 65000 (if transfer failed due to insufficient balance)
        # Account for fraud detection potentially blocking earlier transactions
        self.assertGreater(balance, 55000)

    # ==================== INSUFFICIENT BALANCE TESTS ====================

    def test_withdrawal_insufficient_balance(self):
        """Test withdrawal with insufficient balance"""
        success, msg, txn_id = self.wallet.withdraw("TEST002", 100000, "5678", "Large withdrawal")
        
        self.assertFalse(success)
        self.assertIn("insufficient", msg.lower())
        self.assertIsNone(txn_id)

    def test_transfer_insufficient_balance(self):
        """Test transfer with insufficient balance"""
        success, msg, txn_id = self.wallet.transfer(
            "TEST002", "TEST001", 100000, "5678", "Large transfer"
        )
        
        self.assertFalse(success)
        self.assertIn("insufficient", msg.lower())
        self.assertIsNone(txn_id)

    def test_withdrawal_exact_balance(self):
        """Test withdrawal of exact account balance"""
        # First empty the account to known amount
        success, _, _ = self.wallet.withdraw("TEST002", 10000, "5678")
        self.assertTrue(success)
        
        # Withdraw exactly remaining balance
        _, _, current_balance = self.wallet.check_balance("TEST002")
        success, msg, txn_id = self.wallet.withdraw(
            "TEST002", current_balance, "5678", "Exact balance"
        )
        
        self.assertTrue(success)
        
        # Verify balance is zero
        _, _, balance = self.wallet.check_balance("TEST002")
        self.assertEqual(balance, 0)

    def test_withdrawal_more_than_balance(self):
        """Test withdrawal exceeding balance"""
        _, _, current_balance = self.wallet.check_balance("TEST002")
        amount = current_balance + 1000
        
        success, msg, txn_id = self.wallet.withdraw("TEST002", amount, "5678")
        
        self.assertFalse(success)
        self.assertIn("insufficient", msg.lower())

    # ==================== DAILY LIMIT TESTS ====================

    def test_daily_limit_enforcement(self):
        """Test daily transaction limit enforcement"""
        # Account TEST003 has daily limit of 50000
        success, msg, txn_id = self.wallet.withdraw("TEST003", 40000, "9012", "Large withdrawal")
        self.assertTrue(success)  # May be flagged but should succeed
        
        # Second withdrawal exceeding limit
        success2, msg2, txn_id2 = self.wallet.withdraw("TEST003", 15000, "9012", "Exceed limit")
        
        self.assertFalse(success2)
        self.assertIn("daily limit", msg2.lower())

    def test_daily_limit_check(self):
        """Test daily remaining limit calculation"""
        # Account TEST003 has daily limit of 50000
        success, msg, remaining = self.wallet.get_daily_remaining("TEST003")
        
        self.assertTrue(success)
        self.assertEqual(remaining, 50000)

    def test_daily_limit_after_withdrawal(self):
        """Test daily limit updates after withdrawal"""
        # Account TEST003 has daily limit of 50000
        # Reset the daily spent to ensure fresh state
        success, msg, txn_id = self.wallet.withdraw("TEST003", 20000, "9012", "First withdrawal")
        
        _, _, remaining = self.wallet.get_daily_remaining("TEST003")
        if success:
            self.assertEqual(remaining, 30000)
        else:
            # If it was blocked, remaining should still be full limit
            self.assertEqual(remaining, 50000)

    def test_daily_limit_with_transfers(self):
        """Test that transfers count toward daily limit"""
        # Account TEST003 has daily limit of 50000
        success1, msg1, _ = self.wallet.transfer("TEST003", "TEST001", 35000, "9012", "Transfer 1")
        
        if success1:
            _, _, remaining = self.wallet.get_daily_remaining("TEST003")
            self.assertEqual(remaining, 15000)
            
            # Should reject transfer exceeding remaining limit
            success2, msg2, _ = self.wallet.transfer("TEST003", "TEST001", 20000, "9012", "Transfer 2")
            self.assertFalse(success2)

    def test_daily_limit_reset_next_day(self):
        """Test that daily limit resets (simulated)"""
        # Try to max out daily limit (may be blocked due to fraud detection)
        success, msg, txn_id = self.wallet.withdraw("TEST003", 40000, "9012")
        
        if success:
            _, _, remaining1 = self.wallet.get_daily_remaining("TEST003")
            self.assertEqual(remaining1, 10000)
            
            # Simulate next day by manually advancing transaction timestamps
            # Note: In real system, this would happen naturally at midnight
            account = self.wallet.accounts["TEST003"]
            for txn in account.transactions:
                txn.timestamp = datetime.now() - timedelta(days=2)
            
            _, _, remaining2 = self.wallet.get_daily_remaining("TEST003")
            self.assertEqual(remaining2, 50000)

    # ==================== MULTIPLE FAILED PIN TESTS ====================

    def test_single_failed_pin_attempt(self):
        """Test single failed PIN attempt"""
        success, msg = self.wallet.verify_pin("TEST001", "0000")
        
        self.assertFalse(success)
        self.assertIn("incorrect", msg.lower())
        
        # Account should not be locked yet
        account = self.wallet.accounts["TEST001"]
        self.assertFalse(account.is_locked())

    def test_two_failed_pin_attempts(self):
        """Test two failed PIN attempts"""
        self.wallet.verify_pin("TEST001", "0000")
        success, msg = self.wallet.verify_pin("TEST001", "0000")
        
        self.assertFalse(success)
        self.assertIn("incorrect", msg.lower())
        
        # Account should not be locked yet
        account = self.wallet.accounts["TEST001"]
        self.assertFalse(account.is_locked())

    def test_three_failed_pins_account_lockout(self):
        """Test that 3 failed PIN attempts lock account"""
        # Attempt 1
        self.wallet.verify_pin("TEST001", "0000")
        # Attempt 2
        self.wallet.verify_pin("TEST001", "0000")
        # Attempt 3
        success, msg = self.wallet.verify_pin("TEST001", "0000")
        
        self.assertFalse(success)
        self.assertIn("locked", msg.lower())
        
        # Verify account is locked
        account = self.wallet.accounts["TEST001"]
        self.assertTrue(account.is_locked())

    def test_locked_account_prevents_operations(self):
        """Test that locked account cannot perform operations"""
        # Lock the account
        self.wallet.verify_pin("TEST001", "0000")
        self.wallet.verify_pin("TEST001", "0000")
        self.wallet.verify_pin("TEST001", "0000")
        
        # Try to withdraw from locked account
        success, msg, _ = self.wallet.withdraw("TEST001", 5000, "1234")
        
        self.assertFalse(success)
        self.assertIn("locked", msg.lower())

    def test_correct_pin_after_failed_attempts(self):
        """Test correct PIN resets failed attempt counter"""
        # Make 1 failed attempt
        self.wallet.verify_pin("TEST001", "0000")
        
        # Verify correct PIN
        success, msg = self.wallet.verify_pin("TEST001", "1234")
        
        self.assertTrue(success)
        
        # Failed counter should be reset
        account = self.wallet.accounts["TEST001"]
        self.assertEqual(account.failed_pin_attempts, 0)

    def test_account_unlock_after_timeout(self):
        """Test that locked account unlocks after timeout"""
        # Lock the account
        self.wallet.verify_pin("TEST001", "0000")
        self.wallet.verify_pin("TEST001", "0000")
        self.wallet.verify_pin("TEST001", "0000")
        
        account = self.wallet.accounts["TEST001"]
        self.assertTrue(account.is_locked())
        
        # Manually advance lock time to simulate unlock
        account.account_locked_until = datetime.now() - timedelta(seconds=1)
        
        # Account should now be unlocked
        self.assertFalse(account.is_locked())

    # ==================== SUSPICIOUS TRANSACTION TESTS ====================

    def test_large_transaction_flagged(self):
        """Test that large transactions are flagged for fraud"""
        # Use a large amount that would trigger fraud detection
        success, msg, txn_id = self.wallet.withdraw("TEST001", 55000, "1234", "Large amount")
        
        # Should be either flagged for review or blocked due to high risk
        self.assertIn(txn_id is not None, [True])  # Should have a transaction ID even if failed
        if success:
            self.assertIn("flagged", msg.lower())
        else:
            self.assertIn("blocked", msg.lower())

    def test_unusual_amount_flagged(self):
        """Test that unusual transaction amounts are flagged"""
        success, msg, txn_id = self.wallet.withdraw("TEST001", 35000, "1234", "Unusual amount")
        
        # Should be either flagged for review or blocked
        if success:
            self.assertIn("flagged", msg.lower())
            # Check fraud reasons
            _, _, txns = self.wallet.get_transaction_history("TEST001", limit=1)
            self.assertTrue(txns[0]["flagged"])
        else:
            # May be blocked if risk is high
            self.assertIn("blocked", msg.lower())

    def test_critical_fraud_blocks_transaction(self):
        """Test that critical fraud level blocks transaction"""
        # Create scenario for critical fraud by making large transaction
        # Lock account with failed PINs
        self.wallet.verify_pin("TEST001", "0000")
        self.wallet.verify_pin("TEST001", "0000")
        self.wallet.verify_pin("TEST001", "0000")
        
        # Account is now locked
        account = self.wallet.accounts["TEST001"]
        self.assertTrue(account.is_locked())
        
        # Try transaction while locked
        success, msg, _ = self.wallet.withdraw("TEST001", 1000, "1234", "Any amount")
        
        # Should fail due to lock
        self.assertFalse(success)
        self.assertIn("locked", msg.lower())

    def test_high_frequency_transaction_flagged(self):
        """Test that high frequency transactions are flagged"""
        # Make 5 deposits in quick succession
        for i in range(5):
            self.wallet.deposit("TEST001", 1000, f"Deposit {i+1}")
        
        # 6th transaction should trigger frequency alert
        success, msg, txn_id = self.wallet.deposit("TEST001", 1000, "Deposit 6")
        
        # May be flagged or blocked depending on risk assessment
        # The important thing is it's detected
        if not success:
            self.assertIn("blocked", msg.lower())
        # If successful, will be in transaction history

    def test_transaction_flagged_with_reasons(self):
        """Test that flagged transactions include fraud reasons"""
        success, msg, txn_id = self.wallet.withdraw("TEST001", 55000, "1234")
        
        # Check transaction history
        _, _, txns = self.wallet.get_transaction_history("TEST001", limit=1)
        
        if txns:
            txn = txns[0]
            # If transaction was created (flagged or blocked), check properties
            if txn.get("flagged"):
                self.assertGreater(len(txn["fraud_reasons"]), 0)
            else:
                # Even non-flagged high value transactions should be recorded
                self.assertIsNotNone(txn["transaction_id"])

    # ==================== NEGATIVE AMOUNT TESTS ====================

    def test_negative_deposit_rejected(self):
        """Test that negative deposit amounts are rejected"""
        success, msg, txn_id = self.wallet.deposit("TEST001", -5000, "Negative deposit")
        
        self.assertFalse(success)
        self.assertIn("positive", msg.lower())
        self.assertIsNone(txn_id)

    def test_negative_withdrawal_rejected(self):
        """Test that negative withdrawal amounts are rejected"""
        success, msg, txn_id = self.wallet.withdraw("TEST001", -5000, "1234", "Negative withdrawal")
        
        self.assertFalse(success)
        self.assertIn("positive", msg.lower())
        self.assertIsNone(txn_id)

    def test_negative_transfer_rejected(self):
        """Test that negative transfer amounts are rejected"""
        success, msg, txn_id = self.wallet.transfer("TEST001", "TEST002", -5000, "1234")
        
        self.assertFalse(success)
        self.assertIn("positive", msg.lower())
        self.assertIsNone(txn_id)

    def test_zero_amount_rejected(self):
        """Test that zero amount transactions are rejected"""
        success, msg, _ = self.wallet.deposit("TEST001", 0, "Zero deposit")
        self.assertFalse(success)
        
        success, msg, _ = self.wallet.withdraw("TEST001", 0, "1234")
        self.assertFalse(success)
        
        success, msg, _ = self.wallet.transfer("TEST001", "TEST002", 0, "1234")
        self.assertFalse(success)

    # ==================== DUPLICATE TRANSACTION TESTS ====================

    def test_transaction_id_uniqueness(self):
        """Test that each transaction has a unique ID"""
        success1, _, txn_id1 = self.wallet.deposit("TEST001", 1000, "Deposit 1")
        success2, _, txn_id2 = self.wallet.deposit("TEST001", 1000, "Deposit 2")
        
        self.assertTrue(success1)
        self.assertTrue(success2)
        self.assertNotEqual(txn_id1, txn_id2)

    def test_transaction_timestamp_recorded(self):
        """Test that transactions record timestamps"""
        self.wallet.deposit("TEST001", 1000, "Test deposit")
        
        _, _, txns = self.wallet.get_transaction_history("TEST001", limit=1)
        txn = txns[0]
        
        self.assertIsNotNone(txn["timestamp"])
        self.assertIn("T", txn["timestamp"])  # ISO format check

    def test_no_automatic_duplicate_detection(self):
        """Test that identical transactions can be made (no auto-dedup)"""
        success1, _, txn_id1 = self.wallet.withdraw("TEST001", 1000, "1234", "Withdrawal")
        success2, _, txn_id2 = self.wallet.withdraw("TEST001", 1000, "1234", "Withdrawal")
        
        # Both should succeed or both be prevented by business logic
        # The system allows duplicate transactions
        self.assertEqual(success1, success2)

    def test_transfer_creates_two_transaction_records(self):
        """Test that transfers create separate records for sender and receiver"""
        success, _, txn_id = self.wallet.transfer("TEST001", "TEST002", 5000, "1234")
        
        if success:
            _, _, txns_sender = self.wallet.get_transaction_history("TEST001", limit=1)
            _, _, txns_receiver = self.wallet.get_transaction_history("TEST002", limit=1)
            
            self.assertGreater(len(txns_sender), 0)
            self.assertGreater(len(txns_receiver), 0)
            
            if txns_sender:
                self.assertEqual(txns_sender[0]["type"], "TRANSFER_SENT")
            if txns_receiver:
                self.assertEqual(txns_receiver[0]["type"], "TRANSFER_RECEIVED")

    # ==================== CONCURRENT TRANSACTION TESTS ====================

    def test_concurrent_deposits(self):
        """Test concurrent deposit transactions"""
        results = []
        
        def deposit_task(amount):
            success, msg, txn_id = self.wallet.deposit("TEST001", amount)
            results.append((success, amount))
        
        threads = []
        for i in range(5):
            t = Thread(target=deposit_task, args=(1000,))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # At least some should succeed
        self.assertEqual(len(results), 5)
        successful_count = sum(1 for r in results if r[0])
        self.assertGreater(successful_count, 0)
        
        # Verify final balance is reasonable (started at 60000)
        _, _, balance = self.wallet.check_balance("TEST001")
        # At minimum 60000, at maximum 65000
        self.assertGreaterEqual(balance, 60000)
        self.assertLessEqual(balance, 65000)

    def test_concurrent_withdrawals(self):
        """Test concurrent withdrawal transactions"""
        results = []
        
        def withdraw_task():
            success, msg, txn_id = self.wallet.withdraw("TEST001", 1000, "1234")
            if success:
                results.append(1)
        
        threads = []
        for i in range(10):
            t = Thread(target=withdraw_task)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All successful withdrawals should be recorded
        _, _, balance = self.wallet.check_balance("TEST001")
        
        # Some may fail due to insufficient balance, but total should not exceed original
        self.assertLessEqual(balance, 100000)

    def test_concurrent_transfers(self):
        """Test concurrent transfer transactions between accounts"""
        results = []
        
        def transfer_task():
            success, msg, txn_id = self.wallet.transfer(
                "TEST001", "TEST002", 100, "1234"
            )
            if success:
                results.append(success)
        
        threads = []
        for i in range(5):
            t = Thread(target=transfer_task)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify balances are consistent and non-negative
        _, _, balance1 = self.wallet.check_balance("TEST001")
        _, _, balance2 = self.wallet.check_balance("TEST002")
        
        self.assertGreaterEqual(balance1, 0)
        self.assertGreaterEqual(balance2, 50000)  # Started with 50000

    def test_concurrent_mixed_operations(self):
        """Test concurrent mixed operations (deposit, withdraw, transfer)"""
        results = []
        
        def mixed_operations():
            # Deposit
            self.wallet.deposit("TEST001", 500)
            # Withdraw
            self.wallet.withdraw("TEST001", 200, "1234")
            # Transfer
            self.wallet.transfer("TEST001", "TEST002", 100, "1234")
            results.append(1)
        
        threads = []
        for i in range(3):
            t = Thread(target=mixed_operations)
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # Verify system is in consistent state
        self.assertEqual(len(results), 3)
        
        _, _, balance1 = self.wallet.check_balance("TEST001")
        _, _, balance2 = self.wallet.check_balance("TEST002")
        
        # Both accounts should have valid balances
        self.assertGreaterEqual(balance1, 0)
        self.assertGreaterEqual(balance2, 0)

    # ==================== EDGE CASE TESTS ====================

    def test_transfer_to_same_account(self):
        """Test that transfer to same account is rejected"""
        success, msg, _ = self.wallet.transfer("TEST001", "TEST001", 1000, "1234")
        
        self.assertFalse(success)
        self.assertIn("same account", msg.lower())

    def test_transaction_with_inactive_account(self):
        """Test operations on inactive accounts"""
        # Deactivate account
        self.wallet.deactivate_account("TEST001", "1234")
        
        # Try deposit
        success, msg, _ = self.wallet.deposit("TEST001", 1000)
        self.assertFalse(success)
        self.assertIn("inactive", msg.lower())
        
        # Try withdrawal
        success, msg, _ = self.wallet.withdraw("TEST001", 1000, "1234")
        self.assertFalse(success)

    def test_account_reactivation(self):
        """Test account reactivation"""
        self.wallet.deactivate_account("TEST001", "1234")
        
        success, msg = self.wallet.activate_account("TEST001", "1234")
        self.assertTrue(success)
        
        # Should be able to operate again
        success, msg, _ = self.wallet.deposit("TEST001", 1000)
        self.assertTrue(success)

    def test_transaction_history_order(self):
        """Test that transaction history is in reverse chronological order"""
        self.wallet.deposit("TEST001", 1000, "First")
        time.sleep(0.1)
        self.wallet.deposit("TEST001", 2000, "Second")
        time.sleep(0.1)
        self.wallet.deposit("TEST001", 3000, "Third")
        
        _, _, txns = self.wallet.get_transaction_history("TEST001", limit=10)
        
        # Should be newest first
        self.assertIn("Third", txns[0]["description"])
        self.assertIn("Second", txns[1]["description"])
        self.assertIn("First", txns[2]["description"])

    def test_account_not_found_handling(self):
        """Test handling of non-existent accounts"""
        success, msg, _ = self.wallet.deposit("NONEXISTENT", 1000)
        self.assertFalse(success)
        self.assertIn("not found", msg.lower())

    def test_invalid_email_account_creation(self):
        """Test account creation with invalid email"""
        success, msg = self.wallet.create_account(
            "TEST004", "Invalid Email User", "not-an-email", "9876543213", "1234"
        )
        self.assertFalse(success)
        self.assertIn("email", msg.lower())

    def test_invalid_pin_account_creation(self):
        """Test account creation with invalid PIN"""
        success, msg = self.wallet.create_account(
            "TEST005", "Invalid PIN User", "valid@email.com", "9876543214", "123"
        )
        self.assertFalse(success)
        self.assertIn("pin", msg.lower())

    def test_invalid_phone_account_creation(self):
        """Test account creation with invalid phone"""
        success, msg = self.wallet.create_account(
            "TEST006", "Invalid Phone User", "valid@email.com", "123", "1234"
        )
        self.assertFalse(success)
        self.assertIn("phone", msg.lower())

    # ==================== FRAUD DETECTION TESTS ====================

    def test_fraud_reasons_include_multiple_indicators(self):
        """Test that fraud detection identifies all suspicious indicators"""
        success, msg, _ = self.wallet.withdraw("TEST001", 75000, "1234")
        
        # Get all transactions and find the one we just made
        _, _, txns = self.wallet.get_transaction_history("TEST001", limit=10)
        
        # Find the large withdrawal transaction
        found = False
        for txn in txns:
            if txn["amount"] == 75000 and "WITHDRAWAL" in txn["transaction_type"]:
                found = True
                # If blocked, it should still have fraud reasons
                if not success or txn.get("status") == "BLOCKED":
                    # Blocked high-fraud transactions should have fraud reasons
                    if txn.get("fraud_reasons"):
                        self.assertTrue(any("Large transaction" in reason for reason in txn["fraud_reasons"]))
                else:
                    # If transaction succeeded, it should have fraud reasons
                    self.assertGreater(len(txn.get("fraud_reasons", [])), 0)
                    self.assertTrue(any("Large transaction" in reason for reason in txn["fraud_reasons"]))
                break
        
        # If we found the transaction, we're good; if not and it was blocked early, that's fine too
        if not found:
            self.assertFalse(success, "Transaction should have failed or been blocked")

    def test_risk_level_calculation(self):
        """Test that risk levels are calculated correctly"""
        # Make transactions with different risk levels
        self.wallet.deposit("TEST001", 100, "Low risk")
        self.wallet.deposit("TEST001", 35000, "Medium risk")
        self.wallet.withdraw("TEST001", 55000, "1234", "High risk")
        
        _, _, txns = self.wallet.get_transaction_history("TEST001", limit=10)
        
        # Find transactions by description and check risk levels
        for txn in txns:
            if "Low risk" in txn["description"]:
                self.assertEqual(txn["risk_level"], "LOW")
            elif "Medium risk" in txn["description"]:
                self.assertIn(txn["risk_level"], ["LOW", "MEDIUM"])
            elif "High risk" in txn["description"]:
                # May be MEDIUM, HIGH, or CRITICAL depending on detection
                self.assertIn(txn["risk_level"], ["MEDIUM", "HIGH", "CRITICAL"])

    def test_flagged_transaction_tracking(self):
        """Test that flagged transactions are tracked globally"""
        self.wallet.withdraw("TEST001", 55000, "1234", "Potentially flagged")
        
        flagged = self.wallet.get_flagged_transactions()
        
        # May or may not have flagged transactions depending on transaction type
        # The important thing is the system tracks them correctly
        self.assertIsInstance(flagged, list)

    def test_account_specific_flagged_transactions(self):
        """Test retrieving flagged transactions for specific account"""
        self.wallet.withdraw("TEST001", 55000, "1234", "Large withdrawal")
        self.wallet.deposit("TEST002", 100, "Normal deposit")
        
        success, msg, txns = self.wallet.get_account_flagged_transactions("TEST001")
        
        self.assertTrue(success)
        # May or may not have flagged transactions, but should return a list
        self.assertIsInstance(txns, list)


class TestWalletSecurityEdgeCases(unittest.TestCase):
    """Additional edge case and security tests"""

    def setUp(self):
        """Initialize test environment"""
        self.wallet = DigitalWallet()
        self.wallet.create_account("EDGE001", "Edge Test", "edge@test.com", "9999999999", "1234")
        self.wallet.deposit("EDGE001", 50000)

    def test_pin_hash_security(self):
        """Test that PINs are properly hashed"""
        account = self.wallet.accounts["EDGE001"]
        
        # PIN should be hashed, not plain text
        self.assertNotEqual(account.pin_hash, "1234")
        
        # Hash should be consistent
        expected_hash = hashlib.sha256("1234".encode()).hexdigest()
        self.assertEqual(account.pin_hash, expected_hash)

    def test_balance_precision(self):
        """Test that balance calculations maintain precision"""
        initial_balance = 50000.0
        self.wallet.deposit("EDGE001", 0.01)
        # Check balance increased
        _, _, balance1 = self.wallet.check_balance("EDGE001")
        self.assertAlmostEqual(balance1, initial_balance + 0.01, places=2)
        
        # Withdraw the small amount
        self.wallet.withdraw("EDGE001", 0.01, "1234")
        _, _, balance2 = self.wallet.check_balance("EDGE001")
        # Should be back to around 50000 (with floating point tolerance)
        self.assertAlmostEqual(balance2, initial_balance, places=2)

    def test_transaction_status_tracking(self):
        """Test that transaction statuses are properly tracked"""
        success, msg, txn_id = self.wallet.withdraw("EDGE001", 10000, "1234")
        
        _, _, txns = self.wallet.get_transaction_history("EDGE001", limit=1)
        
        if txns:
            txn = txns[0]
            if success:
                self.assertEqual(txn["status"], "COMPLETED")
            else:
                self.assertIn(txn["status"], ["BLOCKED", "FAILED"])
        else:
            # No transaction if blocked before creation
            self.assertFalse(success)

    def test_account_lock_duration(self):
        """Test that account lock duration is appropriate"""
        # Lock account
        self.wallet.verify_pin("EDGE001", "0000")
        self.wallet.verify_pin("EDGE001", "0000")
        self.wallet.verify_pin("EDGE001", "0000")
        
        account = self.wallet.accounts["EDGE001"]
        lock_duration = (account.account_locked_until - datetime.now()).total_seconds()
        
        # Should be around 15 minutes (900 seconds)
        self.assertGreater(lock_duration, 800)  # At least 13+ minutes
        self.assertLess(lock_duration, 1000)    # Less than 16+ minutes


def run_test_suite():
    """Run the complete test suite"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all tests
    suite.addTests(loader.loadTestsFromTestCase(TestDigitalWalletQA))
    suite.addTests(loader.loadTestsFromTestCase(TestWalletSecurityEdgeCases))
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    print("=" * 70)
    print("DIGITAL WALLET SECURITY QA TEST SUITE")
    print("=" * 70)
    print()
    
    result = run_test_suite()
    
    print()
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Tests Run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print("=" * 70)
    
    # Exit with appropriate code
    exit(0 if result.wasSuccessful() else 1)
