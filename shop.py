from ast import Try
import telebot
import configure
import sqlite3
from telebot import types
import threading
from requests import get
from time import sleep
from SimpleQIWI import *

client = telebot.TeleBot(configure.config['token'])
db = sqlite3.connect('baza.db', check_same_thread=False)
sql = db.cursor()
lock = threading.Lock()
api = QApi(token=configure.config['tokenqiwi'], phone=configure.config['phoneqiwi'])
markdown="""
    *bold text*
    _italic text_
    [text](URL)
    """

#database

sql.execute("""CREATE TABLE IF NOT EXISTS users (id BIGINT, nick TEXT, cash INT, access INT, bought INT)""")
sql.execute("""CREATE TABLE IF NOT EXISTS shop (id INT, name TEXT, price INT, product TEXT, whobuy TEXT)""")
db.commit()

@client.message_handler(commands=['start'])
def start(message):
	try:
		getname = message.from_user.first_name
		cid = message.chat.id
		uid = message.from_user.id

		sql.execute(f"SELECT id FROM users WHERE id = {uid}")
		if sql.fetchone() is None:
			sql.execute(f"INSERT INTO users VALUES ({uid}, '{getname}', 0, 0, 0)")
			client.send_message(cid, f"🛒 | Welcome, {getname}!\nYou are in a bot store\nChange this text!") #change this your shop welcome page
			db.commit()
		else:
			client.send_message(cid, f"⛔️ | You're already registered! Type /help for commands.")
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.message_handler(commands=['profile', 'myinfo', 'myprofile'])
def myprofile(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		if getaccess == 0:
			accessname = 'User'
		elif getaccess == 1:
			accessname = 'Administrator'
		elif getaccess == 777:
			accessname = 'Developer'
		for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
			client.send_message(cid, f"*📇 | Your profile:*\n\n*👤 | Your ID:* {info[0]}\n*💸 | Balance:* {info[2]} ₽\n* 👑 | Access level:* {accessname}\n*🛒 | Products purchased:* {info[4]}\n\n*🗂 To see the list of purchased products type /mybuy*", parse_mode='Markdown')
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.message_handler(commands=['users'])
def allusers(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 1
		if getaccess < accessquery:
			client.send_message(cid, '⚠️ | You dont have access!')
		else:
			text = '*🗃 | List of all users:*\n\n'
			idusernumber = 0
			for info in sql.execute(f"SELECT * FROM users"):
				if info[3] == 0:
					accessname = 'User'
				elif info[3] == 1:
					accessname = 'Administrator'
				elif info[3] == 777:
					accessname = 'Developer'
				idusernumber += 1
				text += f"*{idusernumber}. {info[0]} ({info[1]})*\n*💸 | Balance:* {info[2]} ₽\n*👑 | Access Level:* {accessname}\n*✉️ | Profile:*" + f" [{info[1]}](tg://user?id="+str(info[0])+")\n\n"
			client.send_message(cid, f"{text}",parse_mode='Markdown')
	except:
		client.send_message(cid, f'Error while executing command')
  
@client.message_handler(commands=['mybuy'])
def mybuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		text = '*🗂 | List of purchased items:*\n\n'
		for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
			for infoshop in sql.execute(f"SELECT * FROM shop"):
				if str(info[0]) in infoshop[4]:
					text += f"*{infoshop[0]}. {infoshop[1]}*\nProduct: {infoshop[3]}\n\n"
		client.send_message(cid,f"{text}",parse_mode='Markdown',disable_web_page_preview=True)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.message_handler(commands=['getprofile', 'info'])
def getprofile(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 1
		if getaccess < accessquery:
			client.send_message(cid, '⚠️ | You dont have access!')
		else:
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				msg = client.send_message(cid, f'Enter user ID:\nExample: {info[0]}')
				client.register_next_step_handler(msg, getprofile_next)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def getprofile_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			getprofileid = message.text
			for info in sql.execute(f"SELECT * FROM users WHERE id = {getprofileid}"):
				if info[3] == 0:
					accessname = 'User'
				elif info[3] == 1:
					accessname = 'Administrator'
				elif info[3] == 777:
					accessname = 'Developer'
				client.send_message(cid, f"*📇 | Profile {info[1]}:*\n\n*User ID:* {info[0]}\n*Balance:* {info[2]} ₽\n *Access Level:* {accessname}\n*Products Purchased:* {info[4]}",parse_mode='Markdown')
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.message_handler(commands=['editbuy'])
def editbuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		accessquery = 1
		with lock:
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			getaccess = sql.fetchone()[3]
		if getaccess < 1:
			client.send_message(cid, '⚠️ | You dont have access!')
		else:
			rmk = types.InlineKeyboardMarkup()
			item_name = types.InlineKeyboardButton(text='Name',callback_data='editbuyname')
			item_price = types.InlineKeyboardButton(text='Price',callback_data='editbuyprice')
			item_product = types.InlineKeyboardButton(text='Product',callback_data='editbuyproduct')
			rmk.add(item_name, item_price, item_product)
			msg = client.send_message(cid, f"🔰 | Choose what you want to change:",reply_markup=rmk,parse_mode='Markdown')
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def editbuy_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuynameidproduct
			editbuynameidproduct = int(message.text)
			msg = client.send_message(cid, f"*Enter new product name:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_name_new_name)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def editbuy_name_new_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuynameproduct
			editbuynameproduct = message.text
			for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {editbuynameidproduct}"):
				rmk = types.InlineKeyboardMarkup()
				item_yes = types.InlineKeyboardButton(text='✅', callback_data='editbuynewnametovaryes')
				item_no = types.InlineKeyboardButton(text='❌', callback_data='editbuynewnameproduct')
				rmk.add(item_yes, item_no)
				msg = client.send_message(cid, f"*🔰 | Product name change:*\n\nProduct ID: {editbuynameidtovar}\nOld product name: {infoshop[1]}\nNew product name: {editbuynametovar}\n \nConfirm the changes?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def editbuy_price(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuypriceidproduct
			editbuypriceidproduct = int(message.text)
			msg = client.send_message(cid, f"*Enter new product price:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_price_new_price)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def editbuy_price_new_price(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuypriceproduct
			editbuypricetovar = int(message.text)
			for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {editbuypriceidtovar}"):
				rmk = types.InlineKeyboardMarkup()
				item_yes = types.InlineKeyboardButton(text='✅', callback_data='editbuynewpricetovaryes')
				item_no = types.InlineKeyboardButton(text='❌', callback_data='editbuynewpricetovarno')
				rmk.add(item_yes, item_no)
				msg = client.send_message(cid, f"*🔰 | Product price change data:*\n\nProduct ID: {editbuypriceidtovar}\nOld price: {infoshop[2]}\nNew price: {editbuypricetovar}\n\nConfirm the changes?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def editbuy_product(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuytovaridproduct
			editbuytovaridtovar = int(message.text)
			msg = client.send_message(cid, f"*Enter a new product link:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_product_new_product)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def editbuy_product_new_product(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global editbuyproduct
			editbuyproductovar = message.text
			for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {editbuytovaridtovar}"):
				rmk = types.InlineKeyboardMarkup()
				item_yes = types.InlineKeyboardButton(text='✅', callback_data='editbuynewtovartovaryes')
				item_no = types.InlineKeyboardButton(text='❌', callback_data='editbuynewtovartovarno')
				rmk.add(item_yes, item_no)
				msg = client.send_message(cid, f"*🔰 | Product link change data:*\n\nProduct ID: {editbuytovaridtovar}\nOld link: {infoshop[3]}\nNew link: {editbuytovartovar}\n\nConfirm the changes?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(lambda call: call.data == 'editbuynewtovartovartovarno' or call.data == 'editbuynewtovartovarno')
def editbuy_product_new_callback(call):
	try:
		if call.data == 'editbuynewtovartovaryes':
			sql.execute(f"SELECT * FROM shop WHERE id = {editbuytovaridtovar}")
			sql.execute(f"UPDATE shop SET tovar = '{editbuytovartovar}' WHERE id = {editbuytovaridtovar}")
			db.commit()
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | You have successfully changed the product link to {editbuytovartovar}")
		elif call.data == 'editbuynewtovartovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | You canceled the product link change")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.callback_query_handler(lambda call: call.data == 'editbuynewpricetovaryes' or call.data == 'editbuynewpricetovarno')
def editbuy_price_new_callback(call):
	try:
		if call.data == 'editbuynewpricetovaryes':
			sql.execute(f"SELECT * FROM shop WHERE id = {editbuypriceidtovar}")
			sql.execute(f"UPDATE shop SET price = {editbuypriceidtovar} WHERE id = {editbuypriceidtovar}")
			db.commit()
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | You have successfully changed the price of the item to {editbuypricetovar}")
		elif call.data == 'editbuynewpricetovarno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | You canceled the price change")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')
@client.callback_query_handler(lambda call: call.data == 'editbuynewnameproducts' or call.data == 'editbuynewnameproducts')
def editbuy_name_new_callback(call):
	try:
		if call.data == 'editbuynewnameproducts':
			sql.execute(f"SELECT * FROM shop WHERE id = {editbuynameidtovar}")
			sql.execute(f"UPDATE shop SET name = '{editbuynameproduct}' WHERE id = {editbuynameidproduct}")
			db.commit()
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | You have successfully changed the product name to {editbuynameproduct}")
		elif call.data == 'editbuynewnameproductno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | You canceled the product name change")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')


@client.callback_query_handler(lambda call: call.data == 'editbuyname' or call.data == 'editbuyprice' or call.data == 'editbuyproduct')
def editbuy_first_callback(call):
	try:
		if call.data == 'editbuyname':
			msg = client.send_message(call.message.chat.id, f"*Enter the ID of the product you want to change the name of:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_name)
		elif call.data == 'editbuyprice':
			msg = client.send_message(call.message.chat.id, f"*Enter the ID of the item you want to change the price for:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_price)
		elif call.data == 'editbuyproduct':
			msg = client.send_message(call.message.chat.id, f"*Enter the ID of the product you want to change the link for:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, editbuy_product)
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.message_handler(commands=['rembuy'])
def removebuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		accessquery = 1
		with lock:
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			getaccess = sql.fetchone()[3]
		if getaccess < 1:
			client.send_message(cid, '⚠️ | You dont have access!')
		else:
			msg = client.send_message(cid, f"*Enter the ID of the product you want to delete:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, removebuy_next)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def removebuy_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global removeidproduct
			removeidproduct = int(message.text)
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {removeidtovar}"):
					rmk = types.InlineKeyboardMarkup()
					item_yes = types.InlineKeyboardButton(text='✅',callback_data='removebuytovaryes')
					item_no = types.InlineKeyboardButton(text='❌',callback_data='removebuytovarno')
					rmk.add(item_yes, item_no)
					msg = client.send_message(cid, f"🔰 | Deletion data:\n\nProduct ID: {infoshop[0]}\nProduct name: {infoshop[1]}\nProduct price: {infoshop[2]}\nProduct : {infoshop[3]}\n\nAre you sure you want to delete the product ?"
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(lambda call: call.data == 'removebuytovaryes' or call.data == 'removebuytovarno')
def removebuy_callback(call):
	try:
		if call.data == 'removebuyproducts':
			sql.execute(f"SELECT * FROM shop")
			sql.execute(f"DELETE FROM shop WHERE id = {removeidproduct}")
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✅ | You have successfully deleted the product")
			db.commit()
		elif call.data == 'removebuyproduct':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | You have canceled item deletion")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.message_handler(commands=['addbuy'])
def addbuy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		with lock:
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			getaccess = sql.fetchone()[3]
		if getaccess < 1:
			client.send_message(cid, '⚠️ | You dont have access!')
		else:
			msg = client.send_message(cid, '*Enter Product ID:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_id)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def addbuy_id(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuyid
			addbuyid = message.text
			msg = client.send_message(cid, '*Enter product price:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_price)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def addbuy_price(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuyprice
			addbuyprice = message.text
			msg = client.send_message(cid, '*Enter product name:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_name)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def addbuy_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuyname
			addbuyname = message.text
			msg = client.send_message(cid, '*Enter product link:*',parse_mode='Markdown')
			client.register_next_step_handler(msg, addbuy_result)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def addbuy_result(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global addbuyproduct
			addbuyproduct = message.text
			sql.execute(f"SELECT name FROM shop WHERE name = '{addbuyname}'")
			if sql.fetchone() is None:
				sql.execute(f"INSERT INTO shop VALUES ({addbuyid}, '{addbuyname}', {addbuyprice}, '{addbuyproduct}', '')"))
				db.commit()
				sql.execute(f"SELECT * FROM shop WHERE name = '{addbuyname}'")
				client.send_message(cid, f'✅ | You have successfully added a product\nProduct ID: {sql.fetchone()[0]}\nName: {addbuyname}\nPrice: {addbuyprice}\nProduct link: {addbuyproduct}')
			else:
				client.send_message(cid, f"⛔️ | This item has already been added!")
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.message_handler(commands=['buy'])
def buy(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id

		text = '🛒 | *List of products*\n\n'
		for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
			for infoshop in sql.execute(f"SELECT * FROM shop"):
				text += f"{infoshop[0]}. {infoshop[1]}\nPrice: {infoshop[2]}\n\n"
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✅', callback_data='firstbuytovaryes')
			item_no = types.InlineKeyboardButton(text='❌', callback_data='firstbuyproduct')
			rmk.add(item_yes, item_no)
			msg = client.send_message(cid, f'{text}*Do you want to proceed to buy a product?*',parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def buy_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global commodity
			tovarid = int(message.text)
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {tovarid}"):
					if info[2] < infoshop[2]:
						client.send_message(cid, '⚠️ | You dont have enough funds to purchase the item!\n\nTo top up your account type /donate')
					else:
						rmk = types.InlineKeyboardMarkup()
						item_yes = types.InlineKeyboardButton(text='✅',callback_data='buytovaryes')
						item_no = types.InlineKeyboardButton(text='❌',callback_data='buyproduct')
						rmk.add(item_yes, item_no)
						msg = client.send_message(cid, f"💸 | Do you confirm the purchase of the product?\n\nIt is IMPOSSIBLE to return funds for this product.",reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(lambda call: call.data == 'firstbuygoods' or call.data == 'firstbuygoods')
def firstbuy_callback(call):
	try:
		if call.data == 'firstbuyproducts':
			msg = client.send_message(call.message.chat.id, f"*Enter the ID of the product you want to buy:*",parse_mode='Markdown')
			client.register_next_step_handler(msg, buy_next)
		elif call.data == 'firstbuyproductno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | You canceled your purchase")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.callback_query_handler(lambda call: call.data == 'buytovarno' or call.data == 'buytovarno')
def buy_callback(call):
	try:
		if call.data == 'buy items':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}"):
				for infoshop in sql.execute(f"SELECT * FROM shop WHERE id = {tovarid}"):
					if str(info[0]) not in infoshop[4]:
						cashproduct = int(info[2] - infoshop[2])
						boughtproduct = int(info[4] + 1)
						whobuytovarinttostr = str(info[0])
						whobuytovar = str(infoshop[4] + whobuytovarinttostr + ',')
						sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}")
						client.delete_message(call.message.chat.id, call.message.message_id-0)
						client.send_message(call.message.chat.id, f"✅ | You have successfully purchased the product\n\nProduct name: {infoshop[1]}\nPrice: {infoshop[2]}\n\nProduct: {infoshop[3 ]}\n\nThank you for your purchase!")
						sql.execute(f"UPDATE users SET cash = {cashtovar} WHERE id = {call.from_user.id}")
						sql.execute(f"UPDATE users SET bought = {boughttovar} WHERE id = {call.from_user.id}")
						sql.execute(f"SELECT * FROM shop WHERE id = {tovarid}")
						sql.execute(f"UPDATE shop SET whobuy = '{whobuyproduct}' WHERE id = {tovarid}")
						db.commit()
					else:
						client.delete_message(call.message.chat.id, call.message.message_id-0)
						client.send_message(call.message.chat.id, f"*⛔️ | This product has already been purchased!*\n\nTo see the list of purchased products type /mybuy",parse_mode='Markdown')
		elif call.data == 'buyproduct':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"❌ | You canceled your purchase!")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.message_handler(commands=['donate'])
def donate(message):
	try:
		cid = message.chat.id
		global uid
		uid = message.from_user.id
		msg = client.send_message(cid, f"*💰 | Enter deposit amount:*",parse_mode='Markdown')
		client.register_next_step_handler(msg, donate_value)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def donate_value(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global donatevalue
			global commentdonate
			global getusername
			global getuserdonateid
			getusername = message.from_user.first_name
			getuserdonateid = message.from_user.id
			sql.execute(f"SELECT * FROM users WHERE id = {uid}")
			commentdonate = sql.fetchone()[0]
			donatevalue = int(message.text)
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✅',callback_data='donateyes')
			item_no = types.InlineKeyboardButton(text='❌',callback_data='donateno')
			rmk.add(item_yes, item_no)
			global qiwibalancebe
			qiwibalancebe = api.balance
			msg = client.send_message(cid, f"🔰 | Top-up request successfully created\n\nAre you sure you want to top-up?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def donateyesoplacheno(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		removekeyboard = types.ReplyKeyboardRemove()
		if message.text == '✅ Paid':
			client.send_message(cid, f"✉️ | Your request has been sent to the administrators, please wait for approval and disbursement of funds.",reply_markup=removekeyboard)
			client.send_message(596060542, f"✉️ | User {getusername} paid for a deposit request\n\nUser ID: {getuserdonateid}\nAmount: {donatevalue}₽\nComment: {commentdonate}\n\nYour QIWI balance before: { qiwibalancebe}\nYour QIWI balance is now: {api.balance}\n\nCheck if the payment is correct and then confirm the issuance of funds.\nTo issue funds, write: /giverub")
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(lambda call: call.data == 'donateyes' or call.data == 'donateno')
def donate_result(call):
	try:
		removekeyboard = types.ReplyKeyboardRemove()
		rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
		rmk.add(types.KeyboardButton('✅ Paid'))
		if call.data == 'donateyes':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			msg = client.send_message(call.message.chat.id, f"➖➖➖➖➖➖➖➖➖➖➖➖\n☎️ Payment wallet: +380661696196\n💰 Amount: {donatevalue}₽\n💭 Comment : {commentdonate}\n*⚠️IMPORTANT⚠️* Comment and amount must be *1in1*\n➖➖➖➖➖➖➖➖➖➖➖➖",parse_mode='Markdown',reply_markup=rmk)
			client.register_next_step_handler(msg, donateyesoplacheno)
		elif call.data == 'donateno':
			client.send_message(call.message.chat.id, f"❌ | You have canceled your deposit request",reply_markup=removekeyboard)
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.message_handler(commands=['getcid'])
def getcid(message):
	client.send_message(message.chat.id, f"Chat ID | {message.chat.id}\nYour ID | {message.from_user.id}")

@client.message_handler(commands=['help'])
def helpcmd(message):
	cid = message.chat.id
	uid = message.from_user.id
	with lock:
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
	if getaccess >= 1:
		client.send_message(cid, '*Help for commands:*\n\n/profile - View your profile\n/help - View list of commands\n/buy - Buy goods\n/donate - Refill account\n/mybuy - View the list of purchased goods\n/teh - Contact technical support\n\nAdmin commands:\n\n/getprofile - View someone elses profile\n/access - Give access level\n/giverub - Give money to the balance\n /getid - Get user ID\n/getcid - Get Conference ID\n/addbuy - Add item for sale\n/editbuy - Edit item details\n/rembuy - Delete item\n/ot - Reply to user (send message) ',parse_mode='Markdown')
	else:
		client.send_message(cid, '*Help for commands:*\n\n/profile - View your profile\n/help - View list of commands\n/buy - Buy goods\n/donate - Refill account\n/mybuy - View list of purchased items\n/teh - Contact tech support',parse_mode='Markdown')

@client.message_handler(commands=['access', 'setaccess', 'dostup'])
def setaccess(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		access_query=777
		if getaccess < accessquery:
			client.send_message(cid, f"⚠️ | You dont have access!")
		else:
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				msg = client.send_message(cid, 'Enter user ID:\nExample: 596060542', parse_mode="Markdown")
				client.register_next_step_handler(msg, access_user_id_answer)
	except:
		client.send_message(cid, f'🚫 | Error executing command')
def access_user_id_answer(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global usridaccess
			usridaccess = message.text
			rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
			rmk.add(types.KeyboardButton('User'), types.KeyboardButton('Administrator'), types.KeyboardButton('Developer'))
			msg = client.send_message(cid, 'What access level do you want to issue?:', reply_markup=rmk, parse_mode="Markdown")
			client.register_next_step_handler(msg, access_user_access_answer)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def access_user_access_answer(message):
	try:
		global accessgaved
		global accessgavedname
		cid = message.chat.id
		uid = message.from_user.id
		rmk = types.InlineKeyboardMarkup()
		access_yes = types.InlineKeyboardButton(text='✅',callback_data='setaccessyes')
		access_no = types.InlineKeyboardButton(text='❌',callback_data='setaccessno')
		rmk.add(access_yes, access_no)
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridaccess}"):
			if message.text == "User":
				accessgavedname = "User"
				accessgaved = 0
			elif message.text == "Administrator":
				accessgavedname = "Administrator"
				accessgaved = 1
			elif message.text == "Developer":
				accessgavedname = "Developer"
				accessgaved=777

			client.send_message(cid, f'Data to send:\nUser ID: {usridaccess} ({info[1]})\nAccess level: {message.text}\n\nReally?', reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(lambda call: call.data == 'setaccessyes' or call.data == 'setaccessno')
def access_user_gave_access(call):
	try:
		removekeyboard = types.ReplyKeyboardRemove()
		if call.data == 'setaccesses':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {usridaccess}"):
				sql.execute(f"UPDATE users SET access = {accessgaved} WHERE id = {usridaccess}")
				db.commit()
				client.delete_message(call.message.chat.id, call.message.message_id-0)
				client.send_message(call.message.chat.id, f'✅ | User {info[1]} granted access level {accessgavedname}', reply_markup=removekeyboard)
		elif call.data == 'setaccessno':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {usridaccess}"):
				client.delete_message(call.message.chat.id, call.message.message_id-0)
				client.send_message(call.message.chat.id, f'🚫 | You canceled {accessgavedname} from {info[1]}', reply_markup=removekeyboard)
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.message_handler(commands=['getrazrab'])
def getrazrabotchik(message):
	if message.from_user.id == 596060542:
		sql.execute(f"UPDATE users SET access = 777 WHERE id = 596060542")
		client.send_message(message.chat.id, f"✅ | You have given yourself a Developer")
		db.commit()
	else:
		client.send_message(message.chat.id, f"⛔️ | Permission denied!")

@client.message_handler(commands=['giverub', 'givedonate', 'givebal'])
def giverubles(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		access_query=777
		if getaccess < accessquery:
			client.send_message(cid, f"⚠️ | You dont have access!")
		else:
			for info in sql.execute(f"SELECT * FROM users WHERE id = {uid}"):
				msg = client.send_message(cid, 'Enter user ID:\nExample: 596060542', parse_mode="Markdown")
				client.register_next_step_handler(msg, rubles_user_id_answer)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def rubles_user_id_answer(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global usridrubles
			usridrubles = message.text
			rmk = types.ReplyKeyboardMarkup(resize_keyboard=True)
			rmk.add(types.KeyboardButton('10'), types.KeyboardButton('100'), types.KeyboardButton('1000'), types.KeyboardButton('Different amount'))
			msg = client.send_message(cid, 'Select amount to issue:', reply_markup=rmk, parse_mode="Markdown")
			client.register_next_step_handler(msg, rubles_user_rubles_answer)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def rubles_user_rubles_answer(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		global rublesgavedvalue
		removekeyboard = types.ReplyKeyboardRemove()
		rmk = types.InlineKeyboardMarkup()
		access_yes = types.InlineKeyboardButton(text='✅',callback_data='giverublesyes')
		access_no = types.InlineKeyboardButton(text='❌',callback_data='giverublesno')
		rmk.add(access_yes, access_no)
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
			if message.text == '10':
				rublesgavedvalue = 10
				client.send_message(cid, f'Data to send:\nUser ID: {usridrubles} ({info[1]})\nAmount: {rublesgavedvalue}\n\nCorrect?',reply_markup=rmk)
			elif message.text == '100':
				rublesgavedvalue = 100
				client.send_message(cid, f'Data to send:\nUser ID: {usridrubles} ({info[1]})\nAmount: {rublesgavedvalue}\n\nCorrect?',reply_markup=rmk)
			elif message.text == '1000':
				rublesgavedvalue = 1000
				client.send_message(cid, f'Data to send:\nUser ID: {usridrubles} ({info[1]})\nAmount: {rublesgavedvalue}\n\nCorrect?',reply_markup=rmk)
			elif message.text == 'Another amount':
				msg = client.send_message(cid, f"*Enter amount to send:*",parse_mode='Markdown',reply_markup=removekeyboard)
				client.register_next_step_handler(msg, rubles_user_rubles_answer_other)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def rubles_user_rubles_answer_other(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		global rublesgavedvalue
		rmk = types.InlineKeyboardMarkup()
		access_yes = types.InlineKeyboardButton(text='✅',callback_data='giverublesyes')
		access_no = types.InlineKeyboardButton(text='❌',callback_data='giverublesno')
		rmk.add(access_yes, access_no)
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
			if message.text == message.text:
				rublesgavedvalue = int(message.text)
				client.send_message(cid, f'Data to send:\nUser ID: {usridrubles} ({info[1]})\nAmount: {rublesgavedvalue}\n\nCorrect?',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(func=lambda call: call.data == 'giverublesyes' or call.data == 'giverublesno')
def rubles_gave_rubles_user(call):
	try:
		removekeyboard = types.ReplyKeyboardRemove()
		for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
			rubless = int(info[2] + rublesgavedvalue)
			if call.data == 'giverublesyes':
				for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
					sql.execute(f"UPDATE users SET cash = {rubless} WHERE id = {usridrubles}")
					db.commit()
					client.delete_message(call.message.chat.id, call.message.message_id-0)
					client.send_message(call.message.chat.id, f'✅ | User {info[1]} received {rublesgavedvalue} rubles', reply_markup=removekeyboard)
			elif call.data == 'giverublesno':
				for info in sql.execute(f"SELECT * FROM users WHERE id = {usridrubles}"):
					client.delete_message(call.message.chat.id, call.message.message_id-0)
					client.send_message(call.message.chat.id, f'🚫 | You have canceled the issuance of rubles to the user {info[1]}', reply_markup=removekeyboard)
			client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.message_handler(commands=['teh'])
def teh(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		msg = client.send_message(cid, f"*📨 | Enter the text you want to send to tech support*",parse_mode='Markdown')
		client.register_next_step_handler(msg, teh_next)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def teh_next(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			global techtextbyuser
			global technamebyuser
			global tehidbyuser
			tehidbyuser = int(message.from_user.id)
			tehnamebyuser = str(message.from_user.first_name)
			tehtextbyuser = str(message.text)
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✉️',callback_data='tehsend')
			item_no = types.InlineKeyboardButton(text='❌',callback_data='tehno')
			rmk.add(item_yes, item_no)
			msg = client.send_message(cid, f"✉️ | Send data:\n\nText to send: {tehtextbyuser}\n\nAre you sure you want to send this to tech support?",parse_mode='Markdown',reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(func=lambda call: call.data == 'tehsend' or call.data == 'tehno')
def teh_callback(call):
	try:
		if call.data == 'tehsend':
			for info in sql.execute(f"SELECT * FROM users WHERE id = {call.from_user.id}"):
				client.delete_message(call.message.chat.id, call.message.message_id-0)
				client.send_message(call.message.chat.id, f"✉️ | Your message has been sent to tech support, please wait for a response.")
				client.send_message(596060542, f"✉️ | User {tehnamebyuser} sent a message to tech support\n\nUser ID: {tehidbyuser}\nText: {tehtextbyuser}\n\nTo reply to the user type /ot")
		elif call.data == 'techno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | You canceled the support message")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.message_handler(commands=['ot'])
def sendmsgtouser(message):
	try:
		cid = message.chat.id

		msg = client.send_message(cid, f"👤 | Enter the user ID you want to send a message to:")
		client.register_next_step_handler(msg, sendmsgtouser_next)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def sendmsgtouser_next(message):
	try:
		cid = message.chat.id

		if message.text == message.text:
			global getsendmsgtouserid
			getsendmsgtouserid = int(message.text)
			msg = client.send_message(cid, f"📨 | Enter the text you want to send to the user:")
			client.register_next_step_handler(msg, sendmsgtouser_next_text)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def sendmsgtouser_next_text(message):
	try:
		cid = message.chat.id

		if message.text == message.text:
			global getsendmsgtousertext
			getsendmsgtousertext = str(message.text)
			rmk = types.InlineKeyboardMarkup()
			item_yes = types.InlineKeyboardButton(text='✅',callback_data='sendmsgtouseryes')
			item_no = types.InlineKeyboardButton(text='❌',callback_data='sendmsgtouserno')
			rmk.add(item_yes, item_no)
			msg = client.send_message(cid, f"🔰 | Message send data:\n\nUser ID: {getsendmsgtouserid}\nText to send: {getsendmsgtousertext}\n\nSend message?",reply_markup=rmk)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

@client.callback_query_handler(func=lambda call: call.data == 'sendmsgtouseryes' or call.data == 'sendmsgtouserno')
def sendmsgtouser_callback(call):
	try:
		if call.data == 'sendmsgtouseryes':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"✉️ | Message sent!")
			client.send_message(getsendmsgtouserid, f"✉️ | Admin sent you a message:\n\n{getsendmsgtousertext}")
		elif call.data == 'sendmsgtouserno':
			client.delete_message(call.message.chat.id, call.message.message_id-0)
			client.send_message(call.message.chat.id, f"🚫 | You canceled sending a message to the user")
		client.answer_callback_query(callback_query_id=call.id)
	except:
		client.send_message(call.message.chat.id, f'🚫 | Error executing command')

@client.message_handler(commands=['getid'])
def getiduser(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		sql.execute(f"SELECT * FROM users WHERE id = {uid}")
		getaccess = sql.fetchone()[3]
		accessquery = 1
		if getaccess < accessquery:
			client.send_message(cid, f"⚠️ | You dont have access!")
		else:
			msg = client.send_message(cid, 'Enter username:')
			client.register_next_step_handler(msg, next_getiduser_name)
	except:
		client.send_message(cid, f'🚫 | Error executing command')

def next_getiduser_name(message):
	try:
		cid = message.chat.id
		uid = message.from_user.id
		if message.text == message.text:
			getusername = message.text
			sql.execute(f"SELECT * FROM users WHERE nick = '{getusername}'")
			result = sql.fetchone()[0]
			client.send_message(cid, f'👤 | User ID: {result}')
	except:
		client.send_message(cid, f'🚫 | Error executing command')



client polling(none_stop=True,interval=0)