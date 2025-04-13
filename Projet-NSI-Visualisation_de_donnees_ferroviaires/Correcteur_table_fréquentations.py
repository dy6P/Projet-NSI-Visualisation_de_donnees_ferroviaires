import csv

lecture=[]
with open("data/frequentation gares.csv", encoding="utf-8") as file_obj:
    reader=csv.reader (file_obj)
    for row in reader:
        lecture.append(row)

gares = [["uic_code", "année", "fréquentation"]]
index = 0
for l in range(len(lecture) - 1):
    index += 1
    annee = 2022
    f = 0
    for chaine in lecture[index]:
        lecture[index] = chaine.rsplit(";")
    for i in range(8):
        f += 1
        frequentation = lecture[index][f]
        gares.append([lecture[index][0], annee, frequentation])
        annee -= 1

with open("data-clean/frequentations.csv", "w", encoding="utf-8", newline="") as file_obj:
    frequentation_csv=csv.writer(file_obj)
    for g in gares:
        frequentation_csv.writerow (g)


