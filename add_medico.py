
import sqlite3

a = sqlite3.connect("clinica.db")
b = a.cursor()

b.execute("PRAGMA table_info(agendamentos);")
c = [row[1] for row in b.fetchall()]

if "medico_id" not in c:
    b.execute("ALTER TABLE agendamentos ADD COLUMN medico_id INTEGER;")
    print("Coluna medico_id adicionada com sucesso!")
else:
    print("Coluna medico_id já existia — nada alterado.")

a.commit()
a.close()