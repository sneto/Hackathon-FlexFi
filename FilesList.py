from CsvFile import CsvFile

class FilesList:
    def __init__(self):
        self.Files = []


    def add_file(self, file_name):
        """Add a new file to the list os files"""
        new_file = CsvFile(file_name)
        self.Files.append(new_file)
        return  new_file

    def find_or_create_file(self, file_name):
        """Find os create a file (if not exists)"""
        file = next((x for x in self.Files if x.Name == file_name), None)

        if not file:
            file = self.add_file(file_name)

        return file

    def add_header(self, file_name, header_name):
        """Add a header string to a file"""
        file = self.find_or_create_file(file_name)
        file.add_header(header_name)


    def add_row(self, file_name, row):
        """Add a data row to a file"""
        file = self.find_or_create_file()
        file.add_row(row)

    def set_column_value(self, file_name, column_name, value):
        """Set a column value for a file"""
        file = self.find_or_create_file(file_name)
        file.set_column_value(column_name, value)

    def increment_file_current_index(self, file_name):
        """Increment a file current data row index"""
        file = self.find_or_create_file(file_name)
        file.increment_current_data_index()

    def get_file_current_index(self, file_name):
        """Get the current data row index from a file"""
        file = self.find_or_create_file(file_name)
        return file.get_current_data_index()

