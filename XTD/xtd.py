

#XTD:xnodza00
import sys
from xml.dom.minidom import parse

fO = sys.stdout
fI = sys.stdin
a = 0
b = 0
etc = 0
num = 666
g = 0

(BIT, INT, FLOAT, NVARCHAR, NTEXT) = range(1, 6)

def help():
	print("------------------------------------------------------------------------------\n"
		"./src/xtd.py\n"
		"===\n"
		"--help                 - Show help\n"
		"--input=filename.ext   - Input file with xml\n"
		"--output=filename.ext  - Output file with xml\n"
		"--header='text'        - Header included on the top of the output\n"
		"--etc=num              - Maximal number of columns from the same element type\n"
		"-a                     - Columns from attributes is not created\n"
		"-b                     - More same elements seem like one\n"
		"-g                     - XML with relations are on the output\n"
		"------------------------------------------------------------------------------\n")

def handleArguments():
	global fO
	global fI
	global a
	global b
	global etc
	global num
	global g
	numberOfArg = len(sys.argv)
	countI = 0
	countO = 0
	countH = 0
	countE = 0
	countA = 0
	countB = 0
	countG = 0
	for i in range(1, numberOfArg):
		string = sys.argv[i]
		if((sys.argv[i] == "--help") and (numberOfArg == 2)):
			help()
			sys.exit(0)
		elif(("--output=" in sys.argv[i]) and (countO == 0)):
			x = string.find('=')
			fpO = string[x+1:]
			try:
				if(fpO != ""):
					fO = open(fpO,"w")
			except: 
				sys.stderr.write("Vystupni soubor nejde otevrit\n")
				sys.exit(1)
			countO += + 1
		elif(("--input=" in sys.argv[i]) and (countI == 0)):
			x = string.find('=')
			fpI = string[x+1:]
			try:
				if(fpI != ""):
					fI = open(fpI, "r")
			except:
				sys.stderr.write("Vstupni soubor nejde otevrit\n")
				sys.exit(1)
			countI += 1
		elif(("--header=" in sys.argv[i]) and (countH == 0)):
			x = string.find('=')
			head = string[x+1:]
			fO.write("--")
			fO.write(head)
			fO.write("\n\n")
			countH += 1
		elif(("--etc=" in sys.argv[i]) and (countE == 0) and (countB == 0)):
			x = string.find('=')
			number = string[x+1:]
			countE += 1
			etc = 1
			num = int(number)
		elif((sys.argv[i] == "-a") and (countA == 0)):
			countA += 1
			a = 1
		elif((sys.argv[i] == "-b") and (countB == 0) and (countE == 0)):
			countB += 1
			b = 1
		elif((sys.argv[i] == "-g") and (countG == 0)):
			countG += 1
			g = 1
		else: 
			sys.stderr.write("Spatne zadane parametry !\n")
			sys.exit(1)


#param data hodnota attributu
def dataType(data):
	if (data == '1') or (data == '0') or (data.lower() == 'true') or (data.lower() == 'false'):
		return BIT
	try:
		if int(data):
			return INT
	except: pass
	try:
		if float(data):
			return FLOAT
	except: pass
	return NTEXT

#param data hodnota attributu
def convToText(data):
	if (data == BIT):
		return "BIT"
	elif (data == INT):
		return "INT"
	elif (data == FLOAT):
		return "FLOAT"
	elif (data == NTEXT):
		return "NTEXT"
	elif (data == NVARCHAR):
		return "NVARCHAR"

#funkce vypise vysledny DDL soubor
#param tables tabulka elementu
#param atributy tabulka atributu
def writeTables(tables, atributy):
	global fO
	for i in tables:
		fO.write("CREATE TABLE "+i+"(\n")
		fO.write("prk_"+i+"_id"+" INT PRIMARY KEY")
		for j in atributy[i]:
			fO.write(",\n"+j+" "+ convToText(atributy[i][j]))
		for z in tables[i]:
			fO.write(",\n"+z+"_id INT")
		fO.write("\n);\n")

#funkce projde XML soubor a vytvori tabulky
#param tables tabulka elementu
#param atributy tabulka atributu
#param root hlavni uzel
#param tmp slouzi pro porovnani s root uzlem
def getTable(tables,atributy,root, tmp):
	fk = {}
	#projdeme vsechny poduzly
	for node in tmp.childNodes:
		#pamatujeme si aktualni polozku i rodice
		polozka = node.nodeName.lower()
		parent = node.parentNode.nodeName.lower()
		#jedna se o element
		if node.nodeType == 1:
			#pokud polozka jeste nema v tabulce zaznam, vytvorime ho
			if polozka not in tables.keys():
				tables[polozka] = {}
				atributy[polozka] = {}
			#pokud nebyl zadan parametr -a
			if a == 0:
				for i in range(len(node.attributes)):
					atr = node.attributes.item(i).name.lower()
					atributy[polozka][atr] = dataType(node.attributes.item(i).value)
					if atributy[polozka][atr] == NTEXT:
						atributy[polozka][atr] = NVARCHAR
			if root.nodeName == tmp.nodeName:
				pass
			#jedna se o cizy klic
			else:
				if polozka in fk.keys():
					fk[polozka] += 1
				else:
					fk[polozka] = 1
			getTable(tables,atributy,root, node)
		#jedna se o atribut
		elif node.nodeType == 3:
			if node.data.strip() != "":
				type = dataType(node.data)
				#zajisteni priority datoveho typu
				if "value" in atributy[parent]:
					if atributy[parent]["value"] < type:
						atributy[parent]["value"] = type
				else:
					atributy[parent]["value"] = type
		#jedno se o cizi klic
		if root.nodeName == tmp.nodeName:
			pass
		else:
			#ulozeni cizich klicu do tabulky
			for i in fk:
				if i not in tables[parent]:
					tables[parent][i] = fk[i]
				else:
					if tables[parent][i] < fk[i]:
						tables[parent][i] = fk[i]

#funkce projde tabulku elementu a vytvori relace
#param tables tabulka elementu
def getRelations(tables):
	#vychozi bod
	relations = {}
	new = {}
	#inicializace
	#projdeme kazdou polozku v tabulce
	for i in tables:
		#pokud vztah jeste neni v tabulce vztahu, vytvorime pro nej zaznam
		if i not in relations.keys():
			relations[i] = {}
		#projdeme kazdy atribut v tabulce
		for j in tables[i]:
			#pokud tabulka odkazuje sama na sebe
			if i == j:
				relation = "1:1"
				relations[i][j] = relation
			#pokud vztah jeste neni v tabulce vztahu, vytvorime pro nej zaznam a nainicializujeme vztah
			elif j not in relations.keys():
				relations[j] = {}
				relations[i][j] = "N:1"
				relations[j][i] = "1:N"
			#pokud rodic odkazuje na syna a syn odkazuje na rodice, zapiseme vztah N:M
			elif ((i in relations.keys()) and (j in relations[i].keys())):
				relation = "N:M"
				relations[i][j] = relation
				relations[j][i] = relation
			#pokud rodic odkazuje na syna a syn neodkazuje na rodice, zapiseme vztah N:1
			elif ((i in relations.keys()) and (j not in relations[i].keys())):
				relations[i][j] = "N:1"
				relations[j][i] = "1:N"
			
	
	#tranzitivita
	muzu = True
	#dokud je mozne provest nejakou zmenu
	while muzu:
		#vytvoreni vztahu, ktere odpovidaji tranzitivite
		for a in relations.keys():
			for c in relations[a].keys():
				for b in relations[c].keys():
					if a == b:
						continue
					#pokud je mozne provest nejakou zmenu
					if b not in relations[a].keys():
						#pokud se R(a,c) rovna R(c,b), pak R(a,b) vytvori novy vztah stejny jako mel R(a,c) nebo R(c,b)
						if relations[a][c] == relations[c][b]:
							relation = relations[a][c]
						#pokud ne, zbyva uz jen jedno pravidlo
						else:
							relation = "N:M"
						#pokud vztah jeste neni v tabulce vztahu, pak se vytvori zaznam
						if a not in new:
							new[a] = {}
						new[a][b] = relation
					#uz neni mozne provest nejakou zmenu
					else:	
						muzu = False
		#pridaji se nove vznikle vztahy do tabulky vztahu
		for i in new.keys():
			for j in new[i].keys():
				if i not in relations:
					relations[i] = {}
				relations[i][j] = new[i][j]
					
					
	return relations

#vypsani vystupniho XML souboru s relacemi
#param relations obsahuje tabulku vztahu
def writeXml(relations):
	fO.write('<?xml version="1.0" encoding="UTF-8"?>\n')
	fO.write("<tables>\n")
	for i in relations:
		fO.write('	<table name="'+i+'">\n')
		for j in relations[i]:
			fO.write('		<relation to="'+j+'" relation_type="'+relations[i][j]+'" />\n')
		fO.write('		<relation to="'+i+'" relation_type="1:1" />\n')
		fO.write("	</table>\n")

	fO.write("</tables>\n")


def main():
	global num
	handleArguments()
	tables = {}
	atributy = {}
	delete = []
	append = []
	dom = parse(fI)
	root = dom.firstChild
	tmp = root
	getTable(tables,atributy,root,tmp)
	
	
	#je zadany parametr etc
	if etc == 1:
		for i in tables:
			for j in tables[i]:
				#pokud pocet odkazu z tabulky je vetsi jak num, vytvori se sloupec v odkazovane tabulce
				if tables[i][j] > num:
					tables[j][i] = -1
					delete.append(j)
			for toDel in delete:
				del tables[i][toDel]
			del delete[:]
	
	if g == 1:
		relations = getRelations(tables)
		writeXml(relations)
	else:
		#nebyl zadany parametr b, je treba vytvorit concatenaci cisla s retezcem
		if b == 0:
			for i in tables:
				for j in tables[i]:
					if tables[i][j] > 1:
						for num in range(1, tables[i][j] + 1):
							new = j + str(num)
							append.append(new)
						delete.append(j)
				for toApp in append:
					tables[i][toApp] = 1
				for toDel in delete:
					del tables[i][toDel]
				del append[:]
				del delete[:]
		writeTables(tables, atributy)
	#print(tables)
	sys.exit(0)

main()
