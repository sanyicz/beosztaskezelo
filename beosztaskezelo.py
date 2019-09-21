from tkinter import *
import sqlite3
import random
import xlsxwriter

def kapcsolodas(adatbazis):
    try:
        conn = sqlite3.connect(adatbazis)
        return conn
    except:
        list_var.set(('Hiba az adatbázishoz való kapcsolódáskor.', ))

adatbazis = 'sh_adatbazis.db'
conn = kapcsolodas(adatbazis)
cur = conn.cursor()

napok = ('Hétfő', 'Kedd', 'Szerda', 'Csütörtök', 'Péntek', 'Szombat', 'Vasárnap') #a hét napjai
muszakok = ('8/5:00', '8/5:40', '6/10:40', '8/10:40', '8/10:00', ) #műszakok fajtái
keresek_listaja = (2, 5, 2, 7, 2, ) #első futáskor, ha még nincs adatbázis, ebből tölti fel a kéréseket, később az adattáblából
cur.execute('CREATE TABLE IF NOT EXISTS diakok (diak_id INTEGER PRIMARY KEY, nev TEXT UNIQUE, n_szam INTEGER)') #létrehozza a diakok táblát, ha még nem létezik
nevsor1 = ['Földi Bence', 'Sinkó Attila', 'Paragi Gábor', 'Rácz Tamás', 'Hugyecz Árpád', 'Deák Tibor', 'Molnár Dániel', 'Szabó Flórián',
           'Pataki Ádám', 'Fehér Attila', 'Bányai Gábor', 'Gombár Dávid', 'Gombár Bence', 'Nagy Richárd', 'Hajdú Krisztián', 'Szántó Tibi',
           'Szekretár Krisztián', 'Zombori Feri', 'Pécsi Bence', 'Béniám Balázs', 'Pócsi Péter', 'Bokor Gergő', 'Tóth Norbi', 'Juhász Sándor',
           'Bálint Nándor', 'Bedleg Kristóf', 'Gregor Patrik', 'Józsa Erik', 'Török Attila', 'Nédó Tamás', 
           ] #első futáskor ebből a listából tölti fel a diákok tábláját
for i in nevsor1:
    cur.execute('INSERT OR IGNORE INTO diakok (nev, n_szam) VALUES (?, ?)', (i, 0))
nevsor = [] #ez a tömb tárolja a rendezett névsort, ami a legördülő listához kell
try: 
    cur.execute('SELECT nev FROM diakok')
    tomb = cur.fetchall()
    nevsor1 = []
    for sor in tomb:
        nevsor1.append(sor[0])
    nevsor = sorted(nevsor1)
except:
    nevsor = ['Minta Diák', ] #ha nincs diakok tábla, akkor csinál egy ilyet, hogy ne legyen hiba

cur.execute('CREATE TABLE IF NOT EXISTS napok (nap_id INTEGER PRIMARY KEY, nap TEXT UNIQUE)') #a hét napjait tároló tábla létrehozása
for i in napok: #feltöltés napokkal
    cur.execute('INSERT OR IGNORE INTO napok (nap) VALUES (?)', (i, ))

cur.execute('CREATE TABLE IF NOT EXISTS muszakok (muszak_id INTEGER PRIMARY KEY, muszak TEXT UNIQUE)') #műszakok fajtáit tároló tábla létrehozása
for i in muszakok: #feltöltés műszakokkal
    cur.execute('INSERT  OR IGNORE INTO muszakok (muszak) VALUES (?)', (i, ))

cur.execute('CREATE TABLE IF NOT EXISTS keresek (nap_id INTEGER, muszak_id INTEGER, fo INTEGER, UNIQUE(nap_id, muszak_id), UNIQUE(nap_id, muszak_id, fo))') #melyik nap melyik műszakjába hány fő kell
for i in napok: #kérések tábla kezdeti feltöltése
    cur.execute('SELECT nap_id FROM napok WHERE nap = ?', (i,))
    nap_id = cur.fetchone()[0]
    for j in muszakok:
        cur.execute('SELECT muszak_id FROM muszakok WHERE muszak = ?', (j,))
        muszak_id = cur.fetchone()[0]
        cur.execute('INSERT OR IGNORE INTO keresek (nap_id, muszak_id, fo) VALUES (?, ?, ?)', (nap_id, muszak_id, keresek_listaja[muszak_id - 1])) #a keresek_listaja tömbből

conn.commit() #az adatbázis eddigi módosításainak mentése

def kiir_raeres_nevek(): #kiírja a felületen beállított nevű diák ráérését
    Nev = nev.get() #kiszedi a diák nevét
    aktev = ev.get() #kiszedi az aktuális évet
    akthet = het.get() #kiszedi az aktuális hetet
    cur.execute('SELECT diak_id FROM diakok WHERE nev = ?', (Nev, ))
    Diak_id = cur.fetchone()[0] #kiszedi a diák azonosítóját
    cur.execute('SELECT * FROM raeresek_' + str(aktev) + '_' + str(akthet) + ' WHERE diak_id = ?', (Diak_id, ))
    tomb = [] #ebbe a tömbbe gyűjti a sorokat
    for r in cur.fetchall(): #minden sorra a kurzorból
        tomb.append(row_format('nev_nelkul', r)) #formázza a sort és hozzáadja a tömbhöz
    if not tomb: #ha üres a tömb
        list_var.set(('Nem adott a hétre ráérést.', )) #az azt jelenti, hogy nincs a diáknak ráérése
    else: #ha nem üres
        list_var.set(tomb) #kiírja a tömböt a szövegmezőbe

def keresek_tomb():
    keresek = []
    for i in range(len(napok)):
        keresek.append([])
        for j in range(len(muszakok)):
            keresek[i].append(entries_keresek[i][j].get())
    return keresek

def keresek_ment():
    keresek = keresek_tomb()
    Nap_id = 1
    for i in range(len(napok)):
        Muszak_id = 1
        for j in range(len(muszakok)):
            cur.execute('UPDATE keresek SET fo = ' + str(keresek[i][j]) + ' WHERE nap_id = ' + str(Nap_id) + ' AND muszak_id = ' + str(Muszak_id))
            Muszak_id += 1
        Nap_id += 1
    conn.commit()
    
def raeres_tomb(): #létrehoz egy tömböt a ráérések rögzítésére a checkbuttonok állapotából
    tomb = [] #ebbe a kétdimenziós tömbbe gyűjtjük az értékeket
    for i in range(len(napok)): #minden napra
        tomb.append([]) #új, üres tömböt adunk hozzá
        for j in range(len(muszakok)): #minden műszakra
            tomb[i].append('1' if variables_raeres[i][j].get() else '0') #1-0 értékeket ír a True-False értékek alapján
    return tomb #visszaadja a tömböt

def raerest_lead(): #diák ráérését leadó függvény
    diak_neve = nev.get() #kiszedi a diák nevét
    aktev = ev.get() #kiszedi az aktuális évet
    akthet = het.get() #kiszedi az aktuális hetet
    cur.execute('CREATE TABLE IF NOT EXISTS raeresek_' + str(aktev) + '_' + str(akthet) + ' (diak_id, nap_id, muszak_id, UNIQUE(diak_id, nap_id, muszak_id))') #létrehozza az adott ráérés táblát, amikor az első diák ráérését adjuk meg
    insert_sql = 'INSERT OR IGNORE INTO raeresek_' + str(aktev) + '_' + str(akthet) + ' (diak_id, nap_id, muszak_id) VALUES (?, ?, ?)' #sql parancs stringként
    n_szam = 0 #a héten ráért napok számát tartja számon
    try:
        cur.execute('SELECT diak_id FROM diakok WHERE nev = ?', (diak_neve,)) #kiszedjük a neve alapján az azonosítóját
        diak_id = cur.fetchone()[0] #kiszedi a diák azonosítóját
        raeres = raeres_tomb() #meghívjuk a ráéréseket a checkbuttonok állapotából kiszedő függvényt
        for i in range(len(napok)): #minden napra
            if (int(raeres[i][0]) + int(raeres[i][1]) + int(raeres[i][2])) > 0: #ha az adott napon legalább egy műszakban ráér
                n_szam += 1 #növeljük a ráért napok számát
                for j in range(len(muszakok)): #minden műszakra
                    if raeres[i][j] == '1': #i és j megadja a nap és a műszak azonosítóját
                        cur.execute(insert_sql, (diak_id, i+1, j+1)) #hozzáadja at aktuális ráérések táblához a diák adott ráérését
        cur.execute('UPDATE diakok SET n_szam = ' + str(n_szam) + ' WHERE diak_id = ' + str(diak_id)) #beírjuk a ráért napok számát a diákok táblába (nem tudja, melyik hét)
        conn.commit() #elmenti az adatbázisban történ változásokat
    except:
        list_var.set(('Hiba a ráérés leadásában.', )) #kiírja ezt, ha a try részben vhol hiba van

def row_format(parameter, row): #sort formázó függvény
    '''A row tuple mint paraméter szerkezete: (diák, nap, műszak) azonosítók.'''
    cur.execute('SELECT nev FROM diakok WHERE diak_id = ?', (row[0], ))
    Diak = cur.fetchone()[0] #kiszedi a sorból a diák nevét
    cur.execute('SELECT nap FROM napok WHERE nap_id = ?', (row[1], ))
    Nap = cur.fetchone()[0] #kiszedi a sorból a napot
    cur.execute('SELECT muszak FROM muszakok WHERE muszak_id = ?', (row[2], ))
    Muszak = cur.fetchone()[0] #kiszedi a sorból a műszakot
    if parameter == 'nevek': #ha a paraméter nevek, nevek szerint rendez
        formatted_row = Diak + ': ' + Nap + ', ' + Muszak #stringet hoz létre az adatokból
    elif parameter == 'napok': #ha a paraméter napok, napok szerint rendez
        formatted_row = (Nap, Muszak, Diak) #tuple-t hoz létre az adatokból
    elif parameter == 'nev_nelkul': #az adott diák ráérésének kiíratásához
        formatted_row = Nap + ', ' + Muszak #csak nap és műszak
    return formatted_row

def listaz_raeresek(): #ráéréseket nevek szerint kiíró függvény
    aktev = ev.get() #kiszedi az aktuális évet
    akthet = het.get() #kiszedi az aktuális hetet
    select_sql = 'SELECT * FROM raeresek_' + str(aktev) + '_' + str(akthet) #sql parancs stringként
    try:
        #cur.execute('SELECT COUNT(*) FROM raeresek_' + str(aktev) + '_' + str(akthet))
        #db = cur.fetchone()[0]
        #print('darab', db)
        cur.execute(select_sql) #végrehajtja az sql parancsot
        t = [] #ebbe a tömbbe gyűjti a sorokat
        for r in cur.fetchall(): #minden sorra
            t.append(row_format('nevek', r)) #formázza a sort és hozzáadja a tömbhöz
        list_var.set(t) #kiírja a tömböt
    except:
        list_var.set(('Hiba a raeresek adattáblával.', )) #kíirja ezt, ha a try részben vhol hiba van

def beoszt(nap_id, muszak_id, diak_id, ev, het): #diák beosztása adott év-hét adott nap-műszakjába
    cur.execute('SELECT * FROM keresek WHERE nap_id = ' + str(nap_id) + ' AND muszak_id = ' + str(muszak_id)) #kiszedi adott műszakra még kellő létszámot
    kert = cur.fetchone()[2] #a létszáma a visszakapott tuple 2-es indexű eleme
    cur.execute('SELECT * FROM beosztas_' + str(ev) + '_' + str(het) + ' WHERE nap_id = ' + str(nap_id) + ' AND muszak_id = ' + str(muszak_id))
    beo = cur.fetchall()
    if kert > len(beo): #ha kell még ember az adott műszakba
        cur.execute('INSERT OR IGNORE INTO beosztas_' + str(ev) + '_' + str(het) + ' (diak_id, nap_id, muszak_id) VALUES (?, ?, ?)', (diak_id, nap_id, muszak_id)) #beosztjuk a diákot
        #cur.execute('UPDATE keresek SET fo = ' + str(kert - 1) + ' WHERE nap_id = ' + str(nap_id) + ' AND muszak_id = ' + str(muszak_id)) #csökkentjük a műszakba még kellő létszámot

def beosztas(cur, ev, het, alg): #beosztást készítő belső függvény
    hiany = 0 #a hétre hiányzó emberek számát tartja számon
    if alg == 'brute': #brute force algoritmus, hétfő reggel 8-tól kezd nevek szerint
        for Nap in napok: #minden napra
            cur.execute('SELECT nap_id FROM napok WHERE nap = ?', (Nap,)) #kiszedjük a nap azonosítóját
            Nap_id = cur.fetchone()[0] #az azonosító a visszakapott egyelemű tuple 0-s indexű eleme
            m = 0 #ha fo = keresek_listaja[m], ekkor nem táblából szedjük a szükséges létszámot, hanem az [2, 5, 2, 7, 2] tömbből
            for Muszak in muszakok: #minden műszakra
                cur.execute('SELECT muszak_id FROM muszakok WHERE muszak = ?', (Muszak,)) #kiszedjük a műszak azonosítóját
                Muszak_id = cur.fetchone()[0] #az azonosító a visszakapott egyelemű tuple 0-s indexű eleme
                ids = (Nap_id, Muszak_id)
                fo = keresek_listaja[m] #ennyi ember kell a műszakba összesen
                #print('Nap, műszak, fő:', ids, fo)
                cur.execute('SELECT * FROM raeresek_' + str(ev) + '_' + str(het) + ' WHERE nap_id LIKE ? AND muszak_id LIKE ?', ids) #kiszedjük a ráérő diákok azonosítóit
                diak_ids = []
                for r in cur.fetchall(): #kiszedjük a ráérők azonosítóját
                    diak_ids.append(r[0]) #az azonosító a visszakapott tuple 0-s indexű eleme
                len_diak_ids = len(diak_ids)
                if len_diak_ids >= fo: #ha legalább annyi diák ér rá, mint amennyi kell
                    dlista = random.sample(diak_ids, fo) #random kiválaszunk a ráérők listájából fo darab diákot
                    for i in dlista: #minden diákra
                        try:
                            cur.execute('INSERT OR IGNORE INTO beosztas_' + str(ev) + '_' + str(het) + ' (diak_id, nap_id, muszak_id) VALUES (?, ?, ?)', (i, Nap_id, Muszak_id)) #beosztjuk
                            conn.commit()                    
                        except:
                            print('Beosztáskészítés hiba: nem sikerült az adatbázisba illesztés.')
                            continue
                else: #ha kevesebben érnek rá, mint kell
                    hiany += (fo - len_diak_ids) #növeljük a hiányt az eltérés mértékével
                    for i in range(len_diak_ids): #beosztunk annyi embert, ahányan ráérnek
                        try:
                            cur.execute('INSERT OR IGNORE INTO beosztas_' + str(ev) + '_' + str(het) + ' (diak_id, nap_id, muszak_id) VALUES (?, ?, ?)', (diak_ids[i], Nap_id, Muszak_id)) #beosztjuk
                            conn.commit()
                        except:
                            print('Beosztáskészítés hiba: nem sikerült az adatbázisba illesztés.')
                            continue
                m += 1
    elif alg == 'frommin': #a héten legkevesebb napot ráérővel kezdi a beosztást
        hiany = -1 #nem számolja a hiányokat
        cur.execute('SELECT * FROM diakok ORDER BY n_szam') #a héten ráért napok száma szerint növekvő sorba rendezi a diákokat
        diakok = cur.fetchall() #kiszedi az rendezett tábla összes sorát, vagyis az összes diákot
        for i in diakok: #minden diákra
            diak_id = i[0] #kiszedi a diák azonosítóját (a visszakapott tuple 0-s indexű eleme)
            cur.execute('SELECT * FROM raeresek_' + str(ev) + '_' + str(het) + ' WHERE diak_id = ' + str(diak_id)) #megkeresi, mikor ér rá az adott diák
            for j in cur.fetchall(): #minden ráérésére
                nap_id = j[1] #kiszedi a nap azonosítóját
                muszak_id = j[2] #kiszedi a hét azonosítóját
                beoszt(nap_id, muszak_id, diak_id, ev, het) #beosztja ezzel a függvénnyel
    elif alg == 'random':
        hiany = -1 #nem számolja a hiányokat
        cur.execute('SELECT * FROM raeresek_' + str(ev) + '_' + str(het)) #minden ráérést kiszed
        raeresek = cur.fetchall()
        random.shuffle(raeresek) #random.shuffle works in place and returns None
        for sor in raeresek: #a randomizált ráérések minden sorára
            Diak_id = sor[0]
            Nap_id = sor[1]
            Muszak_id = sor[2]
            cur.execute('SELECT * FROM beosztas_' + str(ev) + '_' + str(het) + ' WHERE nap_id = ' + str(Nap_id) + ' AND muszak_id = ' + str(Muszak_id))
            tomb = cur.fetchall() #az adott műszakba beosztottak
            cur.execute('SELECT fo FROM keresek WHERE nap_id = ' + str(Nap_id) + ' AND muszak_id = ' + str(Muszak_id))
            fo = cur.fetchone()[0] #az adott műszakba kellő létszám
            if len(tomb) < fo: #ha kevesebben vannak beosztva egy műszakba, mint kell
                if not Diak_id in tomb: #ha az adott diák még nincs beosztva az adott műszakba
                    cur.execute('INSERT OR IGNORE INTO beosztas_' + str(ev) + '_' + str(het) + ' (diak_id, nap_id, muszak_id) VALUES (?, ?, ?)', sor)
                    conn.commit()
    for i in range(7): #minden napra
        cur.execute('SELECT nap_id FROM napok WHERE nap = ?', (napok[i],))
        Nap_id = cur.fetchone()[0] #kiszedi az adott nap azonosítóját (fetchone() returns the row as a tuple)
        for j in range(3): #minden műszakra
            cur.execute('SELECT muszak_id FROM muszakok WHERE muszak = ?', (muszakok[j],)) #kiszedi az adott műszak azonosítóját
            Muszak_id = cur.fetchone()[0] #maga a szám így érhető el a kapott tuple-ből
            cur.execute('SELECT diak_id FROM beosztas_' + str(ev) + '_' + str(het) + ' WHERE nap_id = ' + str(Nap_id))
            diak_ids_beo = cur.fetchall() #adott napra beosztottak
            cur.execute('SELECT diak_id FROM raeresek_' + str(ev) + '_' + str(het) + ' WHERE nap_id = ' + str(Nap_id) + ' AND muszak_id = ' + str(Muszak_id))
            diak_ids_raer = cur.fetchall() #adott műszakban ráérők
            for id_ in diak_ids_raer:
                if not id_ in diak_ids_beo:
                    sor = (id_[0], Nap_id, Muszak_id)
                    cur.execute('INSERT OR IGNORE INTO tartalek_' + str(ev) + '_' + str(het) + ' (diak_id, nap_id, muszak_id) VALUES (?, ?, ?)', sor)
    conn.commit()
    print('Hiányzik ' + str(hiany) + ' ember.') #kiírja, hány ember hiányzik a hétre (nem minden algoritmus számolja)

def beosztast_keszit(): #beosztást készítő fő függvény
    aktev = ev.get() #kiszedi az aktuális évet
    akthet = het.get() #kiszedi az aktuális hetet
    aktalg = alg.get() #kiszedi a beállított algoritmust
    cur.execute('DROP TABLE IF EXISTS beosztas_' + str(aktev) + '_' + str(akthet)) #kitörli a beosztás táblát, ha létezik
    sql_create_beo = 'CREATE TABLE beosztas_' + str(aktev) + '_' + str(akthet) + ' (diak_id INTEGER, nap_id INTEGER, muszak_id INTEGER, UNIQUE(diak_id, nap_id), UNIQUE(diak_id, nap_id, muszak_id))'
    cur.execute(sql_create_beo) #létrehozza az adott év-hét-hez tartozó beosztás táblát
    cur.execute('DROP TABLE IF EXISTS tartalek_' + str(aktev) + '_' + str(akthet))
    cur.execute('CREATE TABLE tartalek_' + str(aktev) + '_' + str(akthet) + ' (diak_id INTEGER, nap_id INTEGER, muszak_id INTEGER, UNIQUE(diak_id, nap_id), UNIQUE(diak_id, nap_id, muszak_id))')
    beosztas(cur, aktev, akthet, aktalg) #utolsó paraméter: brute, frommin vagy random

def listaz_beo_napok(): #kiírja a szövegmezőbe a beosztást napok szerint rendezve
    aktev = ev.get() #kiszedi az aktuális évet
    akthet = het.get() #kiszedi az aktuális hetet
    t = [] #ebbe a tömbbe gyűjti a sorokat
    for Nap in napok: #minden napra
        cur.execute('SELECT nap_id FROM napok WHERE nap = ?', (Nap,))
        Nap_id = cur.fetchone()[0] #kiszedi az adott nap azonosítóját (fetchone() returns the row as a tuple)
        for Muszak in muszakok: #minden műszakra
            cur.execute('SELECT muszak_id FROM muszakok WHERE muszak = ?', (Muszak,))
            Muszak_id = cur.fetchone()[0] #kiszedi az adott műszak azonosítóját
            ids = (Nap_id, Muszak_id)
            cur.execute('SELECT diak_id FROM beosztas_' + str(aktev) + '_' + str(akthet) + ' WHERE nap_id = ' + str(Nap_id) + ' AND muszak_id = ' + str(Muszak_id))
            diak_ids = cur.fetchall() #kiszedi az adott diák azonosítóját
            for rows in diak_ids: #minden sorra
                r = (rows[0], Nap_id, Muszak_id) #sort formázó függvény bemenete
                t.append(row_format('napok', r)) #formázza a sort és hozzáadja a tömbhöz
    list_var.set(t) #kiírja a tömböt szövegmezőbe

def export_txt_beo(): #txt-be exportálja a beosztást nevek szerint
    aktev = ev.get() #kiszedi az aktuális évet
    akthet = het.get() #kiszedi az aktuális hetet
    txt = open('beosztas_' + str(aktev) + '_' + str(akthet) + '.txt', 'w') #létrehozza és írásra megnyitja a heti beosztást tartalmazó fájlt
    cur.execute('SELECT * FROM diakok') #diákokat név szerint rendezi
    sorok = cur.fetchall()
    sorok.sort()
    for sor in sorok: #minden diákra
        Diak_id = sor[0]
        Nev = sor[1]
        cur.execute('SELECT nap_id, muszak_id FROM beosztas_' + str(aktev) + '_' + str(akthet) + ' WHERE diak_id = ' + str(Diak_id))
        beo_tomb = cur.fetchall()
        beo_str = str(Nev) + ': '
        for N in beo_tomb:
            Nap = napok[N[0]-1]
            Muszak = muszakok[N[1]-1]
            beo_str = beo_str + Nap + ' ' + Muszak + ', '
        txt.write(beo_str + '\n')

def export_excel_beo(): #excelbe exportálja a beosztást
    aktev = ev.get() #kiszedi az aktuális évet
    akthet = het.get() #kiszedi az aktuális hetet
    workbook = xlsxwriter.Workbook('beosztas_' + str(aktev) + '_' + str(akthet) + '.xlsx') #munkafüzetet hoz létre
    worksheet = workbook.add_worksheet('Beosztás') #munkalapot hoz létre a munkafüzetben
    worksheet_tart = workbook.add_worksheet('Tartalékok')
    worksheet.set_column(0, 7, 20) #0-7. sorokat 20 szélességűre állítja a beosztásos munkalapon
    worksheet_tart.set_column(0, 7, 20) #0-7. sorokat 20 szélességűre állítja a tartalékos munkalapon
    worksheet.write(0, 0, str(aktev) + '. ' + str(akthet) + '. hét')
    for i in range(len(napok)):
        worksheet.write(0, 1+i, napok[i]) #beírjuk a napokat az első sorba
    row1 = 1 #műszakok nevének beírásához kellő sorok kiszámolása
    row2 = 1 + keresek_listaja[0] + 1
    row3 = 1 + keresek_listaja[0] + 1 + keresek_listaja[1] + 1
    row4 = row3 + keresek_listaja[2] + 1
    row5 = row4 + keresek_listaja[3] + 1
    row_list = [row1, row2, row3, row4, row5]
    worksheet.write(row1, 0, muszakok[0]) #beírjuk a műszakokat az első oszlop megfelelő helyeire
    worksheet.write(row2, 0, muszakok[1]) #a megfelelő hely a kért létszámtól függ
    worksheet.write(row3, 0, muszakok[2])
    worksheet.write(row4, 0, muszakok[3])
    worksheet.write(row5, 0, muszakok[4])
    akt_sor2 = 1
    for i in range(len(napok)): #minden napra
        cur.execute('SELECT nap_id FROM napok WHERE nap = ?', (napok[i],))
        Nap_id = cur.fetchone()[0] #kiszedi az adott nap azonosítóját (fetchone() returns the row as a tuple)
        for j in range(len(muszakok)): #minden műszakra
            cur.execute('SELECT muszak_id FROM muszakok WHERE muszak = ?', (muszakok[j],)) #kiszedi az adott műszak azonosítóját
            Muszak_id = cur.fetchone()[0] #maga a szám így érhető el a kapott tuple-ből
            ids = (Nap_id, Muszak_id) #nap- és műszakazonosítók tuple-je
            cur.execute('SELECT diak_id FROM beosztas_' + str(aktev) + '_' + str(akthet) + ' WHERE nap_id = ' + str(Nap_id) + ' AND muszak_id = ' + str(Muszak_id))
            diak_ids_beo = cur.fetchall() #kiszedi az adott diák azonosítóját
            akt_sor = row_list[j] #aktuális használandó sort számolja
            nevek = [] #ebbe a tömbbe gyűjti a neveket
            for k in diak_ids_beo: #minden diákazonosítóra
                cur.execute('SELECT nev FROM diakok WHERE diak_id = ' + str(k[0])) #kiszedi a diák nevét
                kk = cur.fetchone()[0] #k azonosítónak megfelelő név
                nevek.append(kk) #hozzáadjuk a nevet a tömbhöz
            nevek.sort() #ABC-sorrendbe tesszük a neveket
            for nev in nevek: #minden névre a tömbben
                worksheet.write(akt_sor, 1+i, nev) #kiírja a nevet az ecxel megfelelő cellájába
                akt_sor += 1 #az aktuálisan írandó sor száma

            akt_sor_tart = 10*j
            cur.execute('SELECT diak_id FROM tartalek_' + str(aktev) + '_' + str(akthet) + ' WHERE nap_id = ' + str(Nap_id) + ' AND muszak_id = ' + str(Muszak_id))
            diak_ids_tart = cur.fetchall()
            nevek_tart = []
            for d_id in diak_ids_tart:
                cur.execute('SELECT nev FROM diakok WHERE diak_id = ' + str(d_id[0]))
                nev = cur.fetchone()[0]
                nevek_tart.append(nev)
            nevek_tart.sort()
            for nev in nevek_tart:
                worksheet_tart.write(akt_sor_tart, 1+i, nev)
                akt_sor_tart += 1
    workbook.close() #bezárja a munkafüzetet
    
def uj_diak(): #új diákot vesz fel
    diak_nev = nev.get() #kiszedi a beírt nevet
    sql = 'INSERT OR IGNORE INTO diakok (nev, n_szam) VALUES (?, ?)' #sql parancs string-ként
    cur.execute(sql, (diak_nev, 0)) #beírja a diák nevét a táblába
    return cur.lastrowid

def torol_diak(): #diák törlése a névsorból
    diak_nev = nev.get() #kiszedi a beírt nevet
    cur.execute('DELETE FROM diakok WHERE nev = ?', (diak_nev, )) #törli a megfelelő nevű diákot
    
def listaz_diakok(): #diákok névsorát írja ki a szövegemezőbe
    cur.execute('SELECT * FROM diakok') #kiválaszt minden sort a diakok táblából
    tomb = [] #ebben a tömbben lesznek tárolva az adatok
    for r in cur.fetchall(): #minden sorra
        tomb.append(r[1]) #csak a név marad meg
    tomb.sort() #névsorba rendezés
    list_var.set(tomb) #kiírjuk a tömböt a szövegmezőbe

def sugo(): #segítőablakot jelenít meg
    ablak_sugo = Tk() #ablak létrehozása
    ablak_sugo.title('Súgó') #ablak címe
    text = """
Év, hét:
    Meg kell adni, hogy a készítendő beosztás melyik héthez tartozik.
Diákok:
    Névválasztó menü: a már az adatbázisban lévő diákok közül lehet választani.
    Új diák felvétele: nevet beírni a Név mezőbe, majd Új diák felvétele.
    Diák törlése: a beírt/kiválaszott nevet törli az adatbázisból.
    Diákok listája: a jobb oldali szövegmezőbe kiírja az adatbázisban lévő diákok listáját.
Kérések:
    A táblázatban megadható, hogy melyik nap melyik műszakjába hány embert kértek.
    A Mentés gombbal minden hétre rögzíteni kell a kéréseket, mivel a kiírt értékek alapértelmezések, nem mentett értékek.
Ráérések:
    A név kiválasztásával a táblázatban kipipálható, hogy az adott diák melyik nap melyik műszakjaiban ér rá.
    Ráérést lead: elmenti az adatbázisba diák megadott ráéréseit az adott hétre.
    Diák ráérése: kiírja az adott nevű diák adott heti ráérését.
Beosztás:
    Beosztást készít: beosztást készít az adott hétre megadott ráérésekből, a beállított algoritmus szerint.
    Algoritmus: a beosztáskészítő által használt algoritmus kiválasztása.
    Export xls-be: excel táblázatba menti a kiválasztott heti beosztást.
    Export txt-be: szövegfájlba menti az adott heti beosztást névsor szerint.
    Kilépés: menti az adatbázist és kilép.
"""
    Label(ablak_sugo, text=text, justify=LEFT).pack() #fenti szöveg írása az ablakba
    ablak_sugo.mainloop()

def kilep(): #kilépő parancs
    conn.commit() #elmenti az adatbázisban bekövetkezett változásokat
    conn.close() #lezárja az adatbázissal való kapcsolatot
    ablak.destroy() #bezárja az ablakot

def optionmenu_selection_event(event): #ha választunk egy nevet
    for i in range(len(napok)):
        for j in range(len(muszakok)):
            checkbuttons_raeres[i][j].deselect() #kitörli az előzőleg ott lévő pipákat a ráérésekből

ablak = Tk() #létrehozzuk a főablakot
ablak.title('Suli-Host beosztáskezelő')
first_empty_row = 0 #az elemek létrehozásához számon tartja a használandó sort

nev = StringVar() #név változója
nev.set('Válaszd ki a neved.') #a név változó kezdeti értéke
ev = IntVar() #év változója
ev.set(2019)
het = IntVar() #hét változója
het.set(1)
alg = StringVar()
alg.set('random')
algoritmusok = ('random', 'brute', 'frommin')

#év, hét, név választására való címkék és mezők létrehozása
label_fo = Label(ablak, text='BEOSZTÁSKEZELŐ')
label_ev = Label(ablak, text='Év')
entry_ev = Entry(ablak, textvariable=ev, width=12)
label_het = Label(ablak, text='Hét')
entry_het = Entry(ablak, textvariable=het, width=12)
label_nev = Label(ablak, text='Név')
option_nevek = OptionMenu(ablak, nev, *nevsor, command=optionmenu_selection_event) #lenyíló menüből lehet nevet választani
option_nevek.configure(width=20)
#év, hét, név választására való címkék és mezők elhelyezése
label_fo.grid(row=0, column=0, columnspan=2, sticky=W)
first_empty_row += 1
label_ev.grid(row=1, column=1, sticky=E)
entry_ev.grid(row=1, column=2)
label_het.grid(row=1, column=3, sticky=E)
entry_het.grid(row=1, column=4)
label_nev.grid(row=1, column=5, sticky=E)
option_nevek.grid(row=1, column=6, columnspan=2, sticky=W)
first_empty_row += 1

#diákok részhez tartozó címkék és mezők létrehozása
label_diakok = Label(ablak, text='Diákok')
button_diaklista = Button(ablak, text='Diákok listája', width=12, command=listaz_diakok)
button_ujdiak = Button(ablak, text='Új diák', width=12, command=uj_diak)
entry_nev = Entry(ablak, textvariable=nev)
button_toroldiak = Button(ablak, text='Diák törlése', width=12, command=torol_diak)
#diákok részhez tartozó címkék és mezők elhelyezése
label_diakok.grid(row=2, column=0, sticky=W)
first_empty_row += 1
button_diaklista.grid(row=first_empty_row, column=1, columnspan=2)
button_ujdiak.grid(row=first_empty_row, column=3, columnspan=2)
entry_nev.grid(row=first_empty_row, column=5, columnspan=2)
button_toroldiak.grid(row=first_empty_row, column=7, columnspan=2)
first_empty_row += 1

#kérések részhez tartozó címkék és mezők létrehozása
label_keresek = Label(ablak, text='Kérések')
button_keres_ment = Button(ablak, text='Mentés', width=12, command=keresek_ment)
#kérések részhez tartozó címkék és mezők elhelyezése
label_keresek.grid(row=first_empty_row, column=0)
first_empty_row += 1
for i in range(len(napok)):
    Label(ablak, text=napok[i], width=8).grid(row=first_empty_row, column=2+i)
first_empty_row += 1
entries_keresek = []
variables_keresek = []
for i in range(len(napok)):
    entries_keresek.append([])
    variables_keresek.append([])
    for j in range(len(muszakok)):
        variable = IntVar()
        cur.execute('SELECT fo FROM keresek WHERE nap_id = ' + str(i+1) + ' AND muszak_id = ' + str(j+1))
        fo = cur.fetchone()[0]
        variable.set(fo)
        entry = Entry(ablak, textvariable=variable, width=5)
        entry.grid(row=first_empty_row+j, column=2+i) #az indexeket fel kell cserélni, hogy a naponként legyenek tárolva a ráérések
        entries_keresek[i].append(entry)
        variables_keresek[i].append(variable)
for i in range(len(muszakok)):
    Label(ablak, text=muszakok[i]).grid(row=first_empty_row, column=1, sticky=W)
    first_empty_row += 1
button_keres_ment.grid(row=first_empty_row, column=1, columnspan=2)
first_empty_row += 1

#ráérések részhez tartozó címkék és mezők létrehozása
label_raeresek = Label(ablak, text='Ráérések')
button_raerest_lead = Button(ablak, text='Ráérést lead', width=12, command=raerest_lead)
button_raerest_kiir = Button(ablak, text='Ráérések kiírása', width=12, command=listaz_raeresek)
button_raeres_diak = Button(ablak, text='Diák ráérése', width=12, command=kiir_raeres_nevek)
#ráérések részhez tartozó címkék és mezők elhelyezése
label_raeresek.grid(row=first_empty_row, column=0)
first_empty_row += 1
for i in range(len(napok)):
    Label(ablak, text=napok[i], width=8).grid(row=first_empty_row, column=2+i)
first_empty_row += 1
checkbuttons_raeres = []
variables_raeres = []
for i in range(len(napok)):
    checkbuttons_raeres.append([])
    variables_raeres.append([])
    for j in range(len(muszakok)):
        variable = BooleanVar()
        checkbutton = Checkbutton(ablak, variable=variable)
        checkbutton.grid(row=first_empty_row+j, column=2+i) #az indexeket fel kell cserélni, hogy a naponként legyenek tárolva a ráérések
        checkbuttons_raeres[i].append(checkbutton)
        variables_raeres[i].append(variable)
for i in range(len(muszakok)):
    Label(ablak, text=muszakok[i]).grid(row=first_empty_row, column=1, sticky=W)
    first_empty_row += 1
first_empty_row += 1
button_raerest_lead.grid(row=first_empty_row, column=1, columnspan=2)
button_raerest_kiir.grid(row=first_empty_row, column=3, columnspan=2)
button_raeres_diak.grid(row=first_empty_row, column=5, columnspan=2)
first_empty_row += 1

#beosztás részhez tartozó címkék és mezők létrehozása
label_beosztas = Label(ablak, text='Beosztás')
button_beosztas = Button(ablak, text='Beosztást készít', width=12, command=beosztast_keszit)
button_beosztast_kiir = Button(ablak, text='Beosztás kiírása', width=12, command=listaz_beo_napok)
button_export_excel = Button(ablak, text='Export xlsx-be', width=12, command=export_excel_beo)
button_export_txt = Button(ablak, text='Export txt-be', width=12, command=export_txt_beo)
button_sugo = Button(ablak, text='Súgó', width=12, command=sugo)
button_kilepes = Button(ablak, text='Kilépés', width=12, command=kilep)
option_alg = OptionMenu(ablak, alg, *algoritmusok) #lenyíló menüből lehet nevet választani
option_alg.configure(width=12)
#beosztás részhez tartozó címkék és mezők elhelyezése
label_beosztas.grid(row=first_empty_row, column=0)
first_empty_row += 1
button_beosztas.grid(row=first_empty_row, column=1, columnspan=2)
button_beosztast_kiir.grid(row=first_empty_row, column=3, columnspan=2)
button_export_excel.grid(row=first_empty_row, column=5, columnspan=2)
button_sugo.grid(row=first_empty_row, column=7, columnspan=2)
first_empty_row += 1
option_alg.grid(row=first_empty_row, column=1, columnspan=2)
button_export_txt.grid(row=first_empty_row, column=5, columnspan=2)
button_kilepes.grid(row=first_empty_row, column=7, columnspan=2)
first_empty_row += 1

#szövegmező létrehozása és elhelyezése
list_var = StringVar() #szövegmezőhöz tartozó változó
list_var.set(('Nincs kiíratva semmi.', ))
lista = Listbox(ablak, width=30, height=32, listvariable=list_var, selectmode=MULTIPLE) #szövegmező az adatbázis tartalmának kiírásához
lista.grid(row=1, column=9, rowspan=first_empty_row, columnspan=2)

ablak.mainloop()
