from www import myorm

class Admin(myorm.Model):
	__table__='gc_admin'

	a_id = myorm.IntegerField(primary_key=True)
	a_realname = myorm.StringField()
