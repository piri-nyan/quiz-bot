class Quiz():
    def __init__(self, name, **kwargs) -> None:
        self.name = name
        try:
            self.description = kwargs['description']
            self.time = kwargs['time']
        except Exception as e:
            pass
    
    def editing():
        #decorator for commiting to db
        pass
    
    @editing
    def add_question():
        pass

    def complete_question():
        pass

    def get_random_question():
        pass

    @editing
    def delete_question():
        pass

    @editing
    def set_time():
        pass

    @editing
    def add_members():
        pass

    @editing
    def submit_score():
        pass

def main():
    pass

if __name__ == "__main__":
    main()