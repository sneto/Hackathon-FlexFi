import csv

class CsvFile:
    def __init__(self, name):
        self.Name = name
        self.Headers = []
        self.Rows = []
        self.CurrentDataIndex = 0

    def add_header(self, header):
        """Add a header string to this file"""
        if not header in self.Headers:
            self.Headers.append(header)


    def add_row(self, row):
        """Add a data row to this file"""
        self.Rows.append(row)


    def find_or_create_row(self, row_index):
        """Find os create a row in this file"""
        if row_index >= len(self.Rows):
            new_lina = [];
            self.Rows.append(new_lina)

        return self.Rows[row_index]

    def find_column_and_set(self, row, column_index, value):
        """Find the right column and set its value"""
        while column_index >= len(row):
            row.append("")

        row[column_index] = value

    def set_column_value(self, column_name, value):
        """Controls the process of setting a column value"""
        row = self.find_or_create_row(self.CurrentDataIndex)
        column_index = self.Headers.index(column_name)
        if column_index >= 0:
            self.find_column_and_set(row, column_index, value)

    def increment_current_data_index(self):
        """Increments the current data row index"""
        self.CurrentDataIndex += 1


    def get_current_data_index(self):
        """Gets the current data row indes"""
        return self.CurrentDataIndex

    def generate_csv_content_file(self, file_path):
        """Generate a csv file with this file instance data (headers and rows)"""
        with open(file_path, "w+") as file:
            writer = csv.writer(file, quoting=csv.QUOTE_ALL, lineterminator='\n')
            writer.writerow(self.Headers)
            writer.writerows(self.Rows)
            file.close()
            return True
