def file_reader(path = "GPT_pattern.txt"):
    with open(file=rf"{path}", mode='r', buffering=-1, encoding="utf-8") as file:
        pattern_text = file.readlines() 
        return pattern_text
        
def save_to_txt(file_path: str, print_as_finished = True, **kwargs):
        for key, value in kwargs.items():
            file_name = key
            with open(f"{file_path}\\{file_name}.txt", mode="w+", buffering=-1, encoding="utf-8") as file:
                if isinstance(value, (tuple, list)):
                    [file.write(val) for val in value]
                else:
                    file.write(str(value) + "\n\n")
            if print_as_finished == True:
                print("\n")
                print(f"The information has been added to the {file_name}.txt file.")
        



