class AgentMemory:
    def __init__(self, max_history=12):
        self.history = []
        self.max_history = max_history
    
    def add_message(self, role: str, content: str):
        self.history.append({"role": role, "content": content})
        if len(self.history) > self.max_history:
            self.history = [self.history[0]] + self.history[-(self.max_history - 1):]
    
    def set_system_prompt(self, system_content: str):
        system_message = {"role": "system", "content": system_content}
        
        if self.history and self.history[0]["role"] == "system":
            self.history[0] = system_message
        else:
            self.history.insert(0, system_message)
    
    def get_messages(self):
        return self.history
    
    def reset_history(self):
        if self.history and self.history[0]["role"] == "system":
            self.history = [self.history[0]]
        else:
            self.history = []
    
    def get_system_prompt(self):
        if self.history and self.history[0]["role"] == "system":
            return self.history[0]["content"]
        return ""

GLOBAL_MEMORY = AgentMemory(max_history=12)
