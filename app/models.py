from app.database import BaseModel
import peewee as pw
from datetime import datetime

class User(BaseModel):
    """User model for Cartoon Orbit users"""
    username = pw.CharField(unique=True, max_length=50)
    email = pw.CharField(unique=True)
    password_hash = pw.CharField()
    points = pw.IntegerField(default=100)  # Starting points for new users
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)
    last_login = pw.DateTimeField(null=True)
    is_active = pw.BooleanField(default=True)
    
    class Meta:
        table_name = 'users'

class CToon(BaseModel):
    """cToon model - the collectible cards"""
    name = pw.CharField(max_length=100)
    description = pw.TextField(null=True)
    image_url = pw.CharField(max_length=255)
    rarity = pw.CharField(max_length=20, default='common')  # common, rare, golden, holiday
    toon_type = pw.CharField(max_length=20, default='sticker')  # sticker, game, code, ad, holiday
    show_name = pw.CharField(max_length=100, null=True)  # Cartoon Network show
    character_name = pw.CharField(max_length=100, null=True)
    points_cost = pw.IntegerField(default=10)
    is_animated = pw.BooleanField(default=False)
    has_sound = pw.BooleanField(default=False)
    created_at = pw.DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'ctoons'

class UserCToon(BaseModel):
    """User's collection of cToons"""
    user = pw.ForeignKeyField(User, backref='ctoons')
    ctoon = pw.ForeignKeyField(CToon, backref='owners')
    quantity = pw.IntegerField(default=1)
    acquired_at = pw.DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'user_ctoons'
        indexes = (
            (('user', 'ctoon'), True),  # Unique constraint
        )

class CZone(BaseModel):
    """User's personal gallery space"""
    user = pw.ForeignKeyField(User, backref='czone')
    name = pw.CharField(max_length=100, default='My cZone')
    background_url = pw.CharField(max_length=255, null=True)
    description = pw.TextField(null=True)
    is_public = pw.BooleanField(default=True)
    created_at = pw.DateTimeField(default=datetime.now)
    updated_at = pw.DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'czones'

class CZoneItem(BaseModel):
    """Items placed in a cZone"""
    czone = pw.ForeignKeyField(CZone, backref='items')
    ctoon = pw.ForeignKeyField(CToon, backref='czone_placements')
    position_x = pw.IntegerField(default=0)
    position_y = pw.IntegerField(default=0)
    rotation = pw.IntegerField(default=0)
    placed_at = pw.DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'czone_items'

class Buddy(BaseModel):
    """Buddy list relationships"""
    user = pw.ForeignKeyField(User, backref='buddies')
    buddy_user = pw.ForeignKeyField(User, backref='buddy_of')
    added_at = pw.DateTimeField(default=datetime.now)
    
    class Meta:
        table_name = 'buddies'
        indexes = (
            (('user', 'buddy_user'), True),  # Unique constraint
        )

class Auction(BaseModel):
    """Auction system for trading cToons"""
    seller = pw.ForeignKeyField(User, backref='auctions')
    ctoon = pw.ForeignKeyField(CToon, backref='auctions')
    starting_bid = pw.IntegerField()
    current_bid = pw.IntegerField(null=True)
    current_bidder = pw.ForeignKeyField(User, null=True, backref='bids')
    end_time = pw.DateTimeField()
    created_at = pw.DateTimeField(default=datetime.now)
    status = pw.CharField(max_length=20, default='active')  # active, ended, cancelled
    
    class Meta:
        table_name = 'auctions'
