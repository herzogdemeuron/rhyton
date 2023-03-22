# python standard imports
import os
import csv
import json
from datetime import datetime

# rhyton imports
from main import Rhyton


class ExportBase(Rhyton):

    @classmethod
    def prepFile(cls, file, extension):
        if not file:
            now = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file = '{}/{}.{}'.format(Rhyton.HDM_DT_DIR, now, extension.lower())

        directory = os.path.dirname(file)
        if not os.path.exists(directory):
            os.makedirs(directory)

        return file
    
class CsvExporter(ExportBase):
    
    @classmethod
    def write(cls, data, file=None):
        import itertools
        file = cls.prepFile(file, 'csv')
        keys = [d.keys() for d in data]
        headers = sorted(list(set(itertools.chain.from_iterable(keys))))

        with open(file, 'wb') as f:
            writer = csv.DictWriter(
                    f,
                    fieldnames=headers,
                    extrasaction='ignore',
                    dialect='excel')
            writer.writeheader()
            writer.writerows(data)
        
        return file

    @staticmethod
    def append(data, file):
        # try:
        #     with open(file, 'rb') as f:
        #         reader = csv.reader(f, dialect='excel')
        #         headers = next(reader)
        # except FileNotFoundError:
        #     print("File does not exist.")
        
        # if headers:
        #     with open(file, 'a', newline='') as f:
        #         writer = csv.DictWriter(
        #                 f,
        #                 fieldnames=headers,
        #                 extrasaction='ignore',
        #                 dialect='excel')
        #         writer.writerows(data)

        #     return file
        pass


class JsonExporter(ExportBase):
    
    @classmethod
    def write(cls, data, file=None):
        file = cls.prepFile(file, 'json')
        with open(file, 'w') as f:
            f.write(json.dumps(data, encoding="utf-8", ensure_ascii=False))

        return file

    @staticmethod
    def append(data, file):
        with open(file, 'r') as f:
            existingData = json.load(f)
        if existingData:
            existingData = existingData + data
            with open(file, 'w') as f:
                f.write(json.dumps(
                        existingData, encoding="utf-8", ensure_ascii=False))

        return file