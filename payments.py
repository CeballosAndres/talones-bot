from pathlib import Path
import requests
import glob
import os
from numpy import reshape
import ast

class Payments:
    def __init__(self, curp, curt, directory):
        self.url_get_links = 'https://plataformaeducativa.secolima.gob.mx/38C26D9B4BBB0003AC9B599E4285945C/Reporte/ImpresionTalon/Cargar'
        self.url_index = 'https://plataformaeducativa.secolima.gob.mx/38C26D9B4BBB0003AC9B599E4285945C/Reporte/ImpresionTalon/Index'
        self.directory = directory

        if len(curp) < 18:
            raise Exception('Bad format of curp')
        else:
            self.curp = curp
        if len(curt) < 8:
            raise Exception('There are not a curt')
        else:
            self.curt = curt


    def get_last_payment(self):
        all_payments = self.get_all_index()
        return all_payments[1]['QNA_PAGO'] 


    def get_keyboard_paytments(self, quantity, row, column):
        all_payments = self.get_all_index()
        keyboard = [p['QNA_PAGO'] for p in all_payments[1:quantity+1]]
        return reshape(keyboard, (row, column)).tolist()


    def get_all_index(self):
        response = requests.get(self.url_index)
        raw = response.text.split('var JSON_Qna_pago = ')[1].split(';\r')[0]
        return ast.literal_eval(raw)


    def get_payments(self, fortnight):
        query = {'cp': self.curp, 'ct': self.curt, 'q': fortnight, 'pd': ''}
        response = requests.post(self.url_get_links, params=query)
        json_response = response.json()[8:-1]
        return ast.literal_eval(json_response)


    def get_links(self, payments):
        # link structure http://seonline.secolima.gob.mx/fone/Q21171121/Q211422237541.pdf
        # for tag = 0: http://seonline.secolima.gob.mx/fone/ 
        # for tag = 1: http://descargas.secolima.gob.mx/fone/
        # for '2014423': http://seonline.secolima.gob.mx/fone//QAG"             

        links = []
        for payment in payments[1:]:
            row = payment.get('Reg')
            tag, first_id = row.split('|')
            tag = tag[-1]
            first_id = first_id.split(' ')[0]
            second_id = row.split('(')[1].split(',')[0][1:]
            if tag == '1':
                url = 'http://descargas.secolima.gob.mx/fone/'
            else:
                url = 'http://seonline.secolima.gob.mx/fone/'
            links.append( f'{url}{first_id}/Q{second_id}.pdf')
        return links


    def download_files(self, links, fortnight):
        files = []
        for link in links:
            file = requests.get(link, allow_redirects=True)
            payment = link.split('/')[5]
            file_name = '{}_{}_{}'.format(self.curp, fortnight, payment)
            path = Path(self.directory, file_name)
            files.append(path)
            open(path, 'wb').write(file.content)
        return files


    def download(self, fortnight):
        file_exist = [file for file in Path(self.directory).rglob(self.curp+"_"+str(fortnight)+"*")] 
        if len(file_exist) > 0:
            return file_exist

        payments = self.get_payments(fortnight)
        links = self.get_links(payments)
        return self.download_files(links, fortnight)

    def download_last(self):
        return self.download(self.get_last_payment())
