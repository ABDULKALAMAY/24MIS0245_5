"""
Digital Wallet System with Fraud Detection
A comprehensive digital wallet system with account management, 
transaction handling, and advanced fraud detection mechanisms.
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import List, Dict, Optional, Tuple
import hashlib
import re
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


class TransactionType(Enum):
    """Enumeration for different transaction types"""
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER_SENT = "TRANSFER_SENT"
    TRANSFER_RECEIVED = "TRANSFER_RECEIVED"


class FraudRiskLevel(Enum):
    """Enumeration for fraud risk levels"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


@dataclass
class Transaction:
    """Data class representing a single transaction"""
    transaction_id: str
    account_id: str
    transaction_type: TransactionType
    amount: float
    timestamp: datetime
    description: str = ""
    recipient_id: Optional[str] = None
    is_flagged: bool = False
    fraud_risk_level: FraudRiskLevel = FraudRiskLevel.LOW
    fraud_reasons: List[str] = field(default_factory=list)
    status: str = "COMPLETED"  # COMPLETED, PENDING, FAILED, BLOCKED

    def to_dict(self) -> Dict:
        """Convert transaction to dictionary"""
        return {
            "transaction_id": self.transaction_id,
            "account_id": self.account_id,
            "type": self.transaction_type.value,
            "amount": self.amount,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "recipient_id": self.recipient_id,
            "flagged": self.is_flagged,
            "risk_level": self.fraud_risk_level.value,
            "fraud_reasons": self.fraud_reasons,
            "status": self.status
        }


@dataclass
class Account:
    """Data class representing a digital wallet account"""
    account_id: str
    account_holder: str
    email: str
    phone: str
    pin_hash: str
    balance: float = 0.0
    daily_limit: float = 100000.0
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True
    failed_pin_attempts: int = 0
    last_failed_pin_time: Optional[datetime] = None
    account_locked_until: Optional[datetime] = None
    transactions: List[Transaction] = field(default_factory=list)

    def is_locked(self) -> bool:
        """Check if account is locked due to failed PIN attempts"""
        if self.account_locked_until is None:
            return False
        if datetime.now() >= self.account_locked_until:
            self.account_locked_until = None
            self.failed_pin_attempts = 0
            return False
        return True


class FraudDetector:
    """
    Fraud Detection System
    Detects suspicious transactions based on multiple criteria
    """

    def __init__(self):
        self.HIGH_TRANSACTION_AMOUNT = 50000.0
        self.UNUSUAL_TRANSACTION_THRESHOLD = 30000.0
        self.TRANSACTION_FREQUENCY_LIMIT = 5  # Max 5 transactions
        self.TRANSACTION_FREQUENCY_WINDOW = 600  # In 10 minutes (600 seconds)
        self.FAILED_PIN_ATTEMPT_LIMIT = 3
        self.ACCOUNT_LOCK_DURATION = 900  # 15 minutes in seconds

    def detect_fraud(self, account: Account, amount: float, transaction_type: TransactionType) -> Tuple[bool, FraudRiskLevel, List[str]]:
        """
        Detect potential fraud in a transaction
        Returns: (is_flagged, risk_level, fraud_reasons)
        """
        fraud_reasons = []
        risk_scores = []

        # Check for large transaction
        if amount > self.HIGH_TRANSACTION_AMOUNT:
            fraud_reasons.append(f"Large transaction: ${amount} exceeds threshold of ${self.HIGH_TRANSACTION_AMOUNT}")
            risk_scores.append(2)  # Medium risk

        # Check for unusual transaction amount
        if amount > self.UNUSUAL_TRANSACTION_THRESHOLD:
            fraud_reasons.append(f"Unusual amount: ${amount} is significantly higher than typical transactions")
            risk_scores.append(2)  # Medium risk

        # Check transaction frequency (more than 5 transactions in 10 minutes)
        recent_transactions = self._get_recent_transactions(account, self.TRANSACTION_FREQUENCY_WINDOW)
        if len(recent_transactions) >= self.TRANSACTION_FREQUENCY_LIMIT:
            fraud_reasons.append(f"High transaction frequency: {len(recent_transactions)} transactions in 10 minutes")
            risk_scores.append(3)  # High risk

        # Check failed PIN attempts
        if account.failed_pin_attempts > 0:
            fraud_reasons.append(f"Failed PIN attempts detected: {account.failed_pin_attempts} attempts")
            if account.failed_pin_attempts >= 2:
                risk_scores.append(3)  # High risk
            else:
                risk_scores.append(2)  # Medium risk

        # Determine overall risk level
        is_flagged = len(fraud_reasons) > 0
        risk_level = self._calculate_risk_level(risk_scores, len(fraud_reasons))

        return is_flagged, risk_level, fraud_reasons

    def _get_recent_transactions(self, account: Account, time_window_seconds: int) -> List[Transaction]:
        """Get transactions within the specified time window"""
        cutoff_time = datetime.now() - timedelta(seconds=time_window_seconds)
        return [t for t in account.transactions if t.timestamp >= cutoff_time and t.status == "COMPLETED"]

    def _calculate_risk_level(self, risk_scores: List[int], fraud_reasons_count: int) -> FraudRiskLevel:
        """Calculate overall fraud risk level based on scores"""
        if not risk_scores:
            return FraudRiskLevel.LOW
        
        avg_score = sum(risk_scores) / len(risk_scores)
        
        if fraud_reasons_count >= 3 or avg_score >= 3:
            return FraudRiskLevel.CRITICAL
        elif fraud_reasons_count >= 2 or avg_score >= 2.5:
            return FraudRiskLevel.HIGH
        elif fraud_reasons_count >= 1 or avg_score >= 2:
            return FraudRiskLevel.MEDIUM
        return FraudRiskLevel.LOW


class DigitalWallet:
    """
    Main Digital Wallet System
    Manages accounts, transactions, and fraud detection
    """

    def __init__(self):
        self.accounts: Dict[str, Account] = {}
        self.fraud_detector = FraudDetector()
        self.transaction_counter = 0
        self.flagged_transactions: List[Transaction] = []

    # ==================== Account Management ====================

    def create_account(self, account_id: str, account_holder: str, email: str, 
                      phone: str, pin: str, daily_limit: float = 100000.0) -> Tuple[bool, str]:
        """
        Create a new account
        Args:
            account_id: Unique account identifier
            account_holder: Name of account holder
            email: Email address
            phone: Phone number
            pin: 4-digit PIN
            daily_limit: Daily transaction limit (default: 100,000)
        
        Returns:
            (success, message)
        """
        # Validation
        if account_id in self.accounts:
            return False, f"Account {account_id} already exists"
        
        if not self._validate_email(email):
            return False, "Invalid email format"
        
        if not self._validate_phone(phone):
            return False, "Invalid phone format"
        
        if not self._validate_pin(pin):
            return False, "PIN must be exactly 4 digits"
        
        if daily_limit <= 0:
            return False, "Daily limit must be positive"

        # Hash the PIN
        pin_hash = self._hash_pin(pin)

        # Create account
        account = Account(
            account_id=account_id,
            account_holder=account_holder,
            email=email,
            phone=phone,
            pin_hash=pin_hash,
            daily_limit=daily_limit
        )

        self.accounts[account_id] = account
        return True, f"Account {account_id} created successfully for {account_holder}"

    def verify_pin(self, account_id: str, pin: str) -> Tuple[bool, str]:
        """
        Verify account PIN
        Returns:
            (pin_correct, message)
        """
        if account_id not in self.accounts:
            return False, f"Account {account_id} not found"

        account = self.accounts[account_id]

        # Check if account is locked
        if account.is_locked():
            remaining_time = (account.account_locked_until - datetime.now()).total_seconds()
            return False, f"Account locked. Try again in {int(remaining_time)} seconds"

        # Verify PIN
        pin_hash = self._hash_pin(pin)
        if pin_hash == account.pin_hash:
            account.failed_pin_attempts = 0
            account.account_locked_until = None
            return True, "PIN verified successfully"
        else:
            # Record failed attempt
            account.failed_pin_attempts += 1
            account.last_failed_pin_time = datetime.now()

            if account.failed_pin_attempts >= self.fraud_detector.FAILED_PIN_ATTEMPT_LIMIT:
                account.account_locked_until = datetime.now() + timedelta(
                    seconds=self.fraud_detector.ACCOUNT_LOCK_DURATION
                )
                return False, f"Too many failed PIN attempts. Account locked for 15 minutes"

            return False, f"Incorrect PIN. {self.fraud_detector.FAILED_PIN_ATTEMPT_LIMIT - account.failed_pin_attempts} attempts remaining"

    # ==================== Balance Management ====================

    def check_balance(self, account_id: str) -> Tuple[bool, str, float]:
        """
        Check account balance
        Returns:
            (success, message, balance)
        """
        if account_id not in self.accounts:
            return False, f"Account {account_id} not found", 0.0

        account = self.accounts[account_id]
        if not account.is_active:
            return False, "Account is inactive", 0.0

        return True, "Balance retrieved successfully", account.balance

    def get_daily_spent(self, account_id: str) -> float:
        """Get total amount spent today"""
        if account_id not in self.accounts:
            return 0.0

        account = self.accounts[account_id]
        today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_transactions = [
            t for t in account.transactions
            if t.timestamp >= today_start and 
            t.status == "COMPLETED" and
            t.transaction_type in [TransactionType.WITHDRAWAL, TransactionType.TRANSFER_SENT]
        ]
        return sum(t.amount for t in today_transactions)

    def get_daily_remaining(self, account_id: str) -> Tuple[bool, str, float]:
        """
        Get remaining daily limit
        Returns:
            (success, message, remaining_amount)
        """
        if account_id not in self.accounts:
            return False, f"Account {account_id} not found", 0.0

        account = self.accounts[account_id]
        spent = self.get_daily_spent(account_id)
        remaining = account.daily_limit - spent
        return True, "Daily limit retrieved successfully", remaining

    # ==================== Transaction Operations ====================

    def deposit(self, account_id: str, amount: float, description: str = "Deposit") -> Tuple[bool, str, Optional[str]]:
        """
        Deposit money into account
        Args:
            account_id: Target account
            amount: Deposit amount
            description: Transaction description
        
        Returns:
            (success, message, transaction_id)
        """
        if account_id not in self.accounts:
            return False, f"Account {account_id} not found", None

        account = self.accounts[account_id]

        if not account.is_active:
            return False, "Account is inactive", None

        if amount <= 0:
            return False, "Deposit amount must be positive", None

        # Fraud detection for deposit
        is_flagged, risk_level, fraud_reasons = self.fraud_detector.detect_fraud(
            account, amount, TransactionType.DEPOSIT
        )

        # Create transaction
        transaction = self._create_transaction(
            account_id, TransactionType.DEPOSIT, amount, description
        )
        transaction.is_flagged = is_flagged
        transaction.fraud_risk_level = risk_level
        transaction.fraud_reasons = fraud_reasons

        if is_flagged and risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
            transaction.status = "BLOCKED"
            account.transactions.append(transaction)
            self.flagged_transactions.append(transaction)
            return False, f"Transaction blocked due to fraud risk: {', '.join(fraud_reasons)}", transaction.transaction_id

        # Process deposit
        account.balance += amount
        account.transactions.append(transaction)
        
        if is_flagged:
            self.flagged_transactions.append(transaction)
            return True, f"Deposit successful but flagged for review: {', '.join(fraud_reasons)}\nNew balance: ${account.balance:.2f}", transaction.transaction_id

        return True, f"Deposit of ${amount:.2f} successful. New balance: ${account.balance:.2f}", transaction.transaction_id

    def withdraw(self, account_id: str, amount: float, pin: str, description: str = "Withdrawal") -> Tuple[bool, str, Optional[str]]:
        """
        Withdraw money from account
        Args:
            account_id: Account to withdraw from
            amount: Withdrawal amount
            pin: Account PIN
            description: Transaction description
        
        Returns:
            (success, message, transaction_id)
        """
        # Verify PIN
        pin_verified, pin_message = self.verify_pin(account_id, pin)
        if not pin_verified:
            return False, pin_message, None

        if account_id not in self.accounts:
            return False, f"Account {account_id} not found", None

        account = self.accounts[account_id]

        if not account.is_active:
            return False, "Account is inactive", None

        if amount <= 0:
            return False, "Withdrawal amount must be positive", None

        if amount > account.balance:
            return False, f"Insufficient balance. Available: ${account.balance:.2f}", None

        # Check daily limit
        daily_remaining = self.get_daily_remaining(account_id)[2]
        if amount > daily_remaining:
            return False, f"Daily limit exceeded. Remaining: ${daily_remaining:.2f}", None

        # Fraud detection for withdrawal
        is_flagged, risk_level, fraud_reasons = self.fraud_detector.detect_fraud(
            account, amount, TransactionType.WITHDRAWAL
        )

        # Create transaction
        transaction = self._create_transaction(
            account_id, TransactionType.WITHDRAWAL, amount, description
        )
        transaction.is_flagged = is_flagged
        transaction.fraud_risk_level = risk_level
        transaction.fraud_reasons = fraud_reasons

        if is_flagged and risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
            transaction.status = "BLOCKED"
            account.transactions.append(transaction)
            self.flagged_transactions.append(transaction)
            return False, f"Transaction blocked due to fraud risk: {', '.join(fraud_reasons)}", transaction.transaction_id

        # Process withdrawal
        account.balance -= amount
        account.transactions.append(transaction)
        
        if is_flagged:
            self.flagged_transactions.append(transaction)
            return True, f"Withdrawal successful but flagged for review: {', '.join(fraud_reasons)}\nNew balance: ${account.balance:.2f}", transaction.transaction_id

        return True, f"Withdrawal of ${amount:.2f} successful. New balance: ${account.balance:.2f}", transaction.transaction_id

    def transfer(self, from_account_id: str, to_account_id: str, amount: float, pin: str, 
                description: str = "Transfer") -> Tuple[bool, str, Optional[str]]:
        """
        Transfer money between accounts
        Args:
            from_account_id: Source account
            to_account_id: Destination account
            amount: Transfer amount
            pin: Source account PIN
            description: Transaction description
        
        Returns:
            (success, message, transaction_id)
        """
        # Verify PIN
        pin_verified, pin_message = self.verify_pin(from_account_id, pin)
        if not pin_verified:
            return False, pin_message, None

        if from_account_id not in self.accounts:
            return False, f"Source account {from_account_id} not found", None

        if to_account_id not in self.accounts:
            return False, f"Destination account {to_account_id} not found", None

        if from_account_id == to_account_id:
            return False, "Cannot transfer to the same account", None

        from_account = self.accounts[from_account_id]
        to_account = self.accounts[to_account_id]

        if not from_account.is_active:
            return False, "Source account is inactive", None

        if not to_account.is_active:
            return False, "Destination account is inactive", None

        if amount <= 0:
            return False, "Transfer amount must be positive", None

        if amount > from_account.balance:
            return False, f"Insufficient balance. Available: ${from_account.balance:.2f}", None

        # Check daily limit
        daily_remaining = self.get_daily_remaining(from_account_id)[2]
        if amount > daily_remaining:
            return False, f"Daily limit exceeded. Remaining: ${daily_remaining:.2f}", None

        # Fraud detection for transfer
        is_flagged, risk_level, fraud_reasons = self.fraud_detector.detect_fraud(
            from_account, amount, TransactionType.TRANSFER_SENT
        )

        # Create transactions
        transfer_id = self._generate_transaction_id()
        
        from_transaction = self._create_transaction(
            from_account_id, TransactionType.TRANSFER_SENT, amount, 
            f"{description} to {to_account_id}"
        )
        from_transaction.transaction_id = transfer_id
        from_transaction.recipient_id = to_account_id
        from_transaction.is_flagged = is_flagged
        from_transaction.fraud_risk_level = risk_level
        from_transaction.fraud_reasons = fraud_reasons

        to_transaction = self._create_transaction(
            to_account_id, TransactionType.TRANSFER_RECEIVED, amount,
            f"{description} from {from_account_id}"
        )
        to_transaction.transaction_id = transfer_id
        to_transaction.recipient_id = from_account_id
        to_transaction.fraud_risk_level = risk_level

        if is_flagged and risk_level in [FraudRiskLevel.HIGH, FraudRiskLevel.CRITICAL]:
            from_transaction.status = "BLOCKED"
            to_transaction.status = "BLOCKED"
            from_account.transactions.append(from_transaction)
            to_account.transactions.append(to_transaction)
            self.flagged_transactions.append(from_transaction)
            return False, f"Transfer blocked due to fraud risk: {', '.join(fraud_reasons)}", transfer_id

        # Process transfer
        from_account.balance -= amount
        to_account.balance += amount
        from_account.transactions.append(from_transaction)
        to_account.transactions.append(to_transaction)

        if is_flagged:
            self.flagged_transactions.append(from_transaction)
            return True, f"Transfer successful but flagged for review: {', '.join(fraud_reasons)}", transfer_id

        return True, f"Transfer of ${amount:.2f} to {to_account_id} successful", transfer_id

    # ==================== Transaction History ====================

    def get_transaction_history(self, account_id: str, limit: int = 10) -> Tuple[bool, str, List[Dict]]:
        """
        Get transaction history for an account
        Args:
            account_id: Account ID
            limit: Maximum number of transactions to return
        
        Returns:
            (success, message, transactions_list)
        """
        if account_id not in self.accounts:
            return False, f"Account {account_id} not found", []

        account = self.accounts[account_id]
        transactions = sorted(account.transactions, key=lambda t: t.timestamp, reverse=True)[:limit]
        
        return True, f"Retrieved {len(transactions)} transactions", [t.to_dict() for t in transactions]

    def get_flagged_transactions(self) -> List[Dict]:
        """Get all flagged transactions in the system"""
        return [t.to_dict() for t in self.flagged_transactions]

    def get_account_flagged_transactions(self, account_id: str) -> Tuple[bool, str, List[Dict]]:
        """Get flagged transactions for a specific account"""
        if account_id not in self.accounts:
            return False, f"Account {account_id} not found", []

        account = self.accounts[account_id]
        flagged = [t for t in account.transactions if t.is_flagged]
        
        return True, f"Retrieved {len(flagged)} flagged transactions", [t.to_dict() for t in flagged]

    # ==================== Utility Methods ====================

    def _hash_pin(self, pin: str) -> str:
        """Hash a PIN using SHA-256"""
        return hashlib.sha256(pin.encode()).hexdigest()

    def _validate_pin(self, pin: str) -> bool:
        """Validate PIN format (must be 4 digits)"""
        return bool(re.match(r'^\d{4}$', pin))

    def _validate_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _validate_phone(self, phone: str) -> bool:
        """Validate phone format"""
        # Accept 10-15 digit phone numbers with optional spaces and hyphens
        pattern = r'^[\d\s\-\(\)]{10,15}$'
        return bool(re.match(pattern, phone))

    def _generate_transaction_id(self) -> str:
        """Generate a unique transaction ID"""
        self.transaction_counter += 1
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"TXN{timestamp}{self.transaction_counter:06d}"

    def _create_transaction(self, account_id: str, transaction_type: TransactionType, 
                           amount: float, description: str) -> Transaction:
        """Create a new transaction object"""
        return Transaction(
            transaction_id=self._generate_transaction_id(),
            account_id=account_id,
            transaction_type=transaction_type,
            amount=amount,
            timestamp=datetime.now(),
            description=description
        )

    # ==================== Account Management ====================

    def get_account_info(self, account_id: str) -> Tuple[bool, str, Optional[Dict]]:
        """Get account information"""
        if account_id not in self.accounts:
            return False, f"Account {account_id} not found", None

        account = self.accounts[account_id]
        return True, "Account info retrieved", {
            "account_id": account.account_id,
            "account_holder": account.account_holder,
            "email": account.email,
            "phone": account.phone,
            "balance": account.balance,
            "daily_limit": account.daily_limit,
            "daily_spent": self.get_daily_spent(account_id),
            "created_at": account.created_at.isoformat(),
            "is_active": account.is_active,
            "is_locked": account.is_locked(),
            "transaction_count": len(account.transactions)
        }

    def deactivate_account(self, account_id: str, pin: str) -> Tuple[bool, str]:
        """Deactivate an account"""
        pin_verified, pin_message = self.verify_pin(account_id, pin)
        if not pin_verified:
            return False, pin_message

        if account_id not in self.accounts:
            return False, f"Account {account_id} not found"

        account = self.accounts[account_id]
        account.is_active = False
        return True, f"Account {account_id} deactivated successfully"

    def activate_account(self, account_id: str, pin: str) -> Tuple[bool, str]:
        """Activate an account"""
        pin_verified, pin_message = self.verify_pin(account_id, pin)
        if not pin_verified:
            return False, pin_message

        if account_id not in self.accounts:
            return False, f"Account {account_id} not found"

        account = self.accounts[account_id]
        account.is_active = True
        return True, f"Account {account_id} activated successfully"


# ==================== Example Usage ====================

if __name__ == "__main__":
    # Initialize wallet system
    wallet = DigitalWallet()
    
    print("=" * 60)
    print("DIGITAL WALLET SYSTEM - DEMONSTRATION")
    print("=" * 60)

    # Create accounts
    print("\n1. CREATING ACCOUNTS")
    print("-" * 60)
    success, msg = wallet.create_account("ACC001", "Alice Johnson", "alice@example.com", "9876543210", "1234")
    print(f"✓ {msg}" if success else f"✗ {msg}")
    
    success, msg = wallet.create_account("ACC002", "Bob Smith", "bob@example.com", "9876543211", "5678")
    print(f"✓ {msg}" if success else f"✗ {msg}")

    # Deposit money
    print("\n2. DEPOSITING MONEY")
    print("-" * 60)
    success, msg, txn_id = wallet.deposit("ACC001", 100000, "Initial deposit")
    print(f"✓ {msg}" if success else f"✗ {msg}")
    
    success, msg, txn_id = wallet.deposit("ACC002", 50000, "Initial deposit")
    print(f"✓ {msg}" if success else f"✗ {msg}")

    # Check balance
    print("\n3. CHECKING BALANCE")
    print("-" * 60)
    success, msg, balance = wallet.check_balance("ACC001")
    print(f"✓ Account ACC001 Balance: ${balance:.2f}" if success else f"✗ {msg}")

    # Perform withdrawal
    print("\n4. WITHDRAWAL")
    print("-" * 60)
    success, msg, txn_id = wallet.withdraw("ACC001", 5000, "1234", "ATM withdrawal")
    print(f"✓ {msg}" if success else f"✗ {msg}")

    # Money transfer
    print("\n5. MONEY TRANSFER")
    print("-" * 60)
    success, msg, txn_id = wallet.transfer("ACC001", "ACC002", 15000, "1234", "Payment for services")
    print(f"✓ {msg}" if success else f"✗ {msg}")

    # Daily limit check
    print("\n6. DAILY TRANSACTION LIMIT")
    print("-" * 60)
    success, msg, remaining = wallet.get_daily_remaining("ACC001")
    print(f"✓ Remaining daily limit: ${remaining:.2f}" if success else f"✗ {msg}")

    # Transaction history
    print("\n7. TRANSACTION HISTORY")
    print("-" * 60)
    success, msg, transactions = wallet.get_transaction_history("ACC001", limit=5)
    if success:
        print(f"✓ Retrieved {len(transactions)} transactions:")
        for i, txn in enumerate(transactions, 1):
            print(f"  {i}. {txn['type']:20s} | ${txn['amount']:10.2f} | {txn['timestamp']}")
    else:
        print(f"✗ {msg}")

    # Account information
    print("\n8. ACCOUNT INFORMATION")
    print("-" * 60)
    success, msg, info = wallet.get_account_info("ACC001")
    if success:
        print(f"✓ Account: {info['account_holder']}")
        print(f"  Balance: ${info['balance']:.2f}")
        print(f"  Daily Spent: ${info['daily_spent']:.2f}")
        print(f"  Daily Limit: ${info['daily_limit']:.2f}")
        print(f"  Active: {info['is_active']}")
        print(f"  Transactions: {info['transaction_count']}")

    # Fraud detection demo
    print("\n9. FRAUD DETECTION - LARGE TRANSACTION")
    print("-" * 60)
    success, msg, txn_id = wallet.withdraw("ACC001", 75000, "1234", "Large withdrawal")
    print(f"{'✓' if success else '✗'} {msg}")

    # Fraud detection demo - Multiple failed PIN attempts
    print("\n10. FRAUD DETECTION - FAILED PIN ATTEMPTS")
    print("-" * 60)
    for i in range(4):
        success, msg = wallet.verify_pin("ACC001", "0000")
        print(f"{'✓' if success else '✗'} Attempt {i+1}: {msg}")

    # View flagged transactions
    print("\n11. FLAGGED TRANSACTIONS (FRAUD ALERTS)")
    print("-" * 60)
    flagged = wallet.get_flagged_transactions()
    if flagged:
        print(f"✓ Found {len(flagged)} flagged transactions:")
        for txn in flagged[:3]:
            print(f"  ID: {txn['transaction_id']}")
            print(f"  Risk Level: {txn['risk_level']}")
            print(f"  Reasons: {', '.join(txn['fraud_reasons'])}")
            print()
    else:
        print("✓ No flagged transactions")

    print("=" * 60)
    print("DEMONSTRATION COMPLETE")
    print("=" * 60)
