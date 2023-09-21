
import tkinter
import tkinter.messagebox
import customtkinter
from wf_get_status_and_versions import *


customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        workflowId = ""
        dataowner = ""
        environment =""
        auth = ""

        # configure window
        self.title("Workflow Status Getter")
        self.geometry(f"{1100}x{580}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, padx = 10, pady = 10, sticky="nsew")

        #row 0
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Load Workflow", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        #row 1,2
        self.workflow_id_label = customtkinter.CTkLabel(self.sidebar_frame, text="Workflow ID:", anchor="w")
        self.workflow_id_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.workflow_id = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Workflow ID")
        self.workflow_id.grid(row=2, column=0, padx=20, pady=10)

        #row 3,4
        self.workflow_dataowner_label = customtkinter.CTkLabel(self.sidebar_frame, text="DataOwner ID:", anchor="w")
        self.workflow_dataowner_label.grid(row=3, column=0, padx=20, pady=(10, 0))
        self.workflow_dataowner = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Environment Specific")
        self.workflow_dataowner.grid(row=4, column=0, padx=20, pady=10)

        #row 5,6
        self.environment_selector_label = customtkinter.CTkLabel(self.sidebar_frame, text="Environment:", anchor="w")
        self.environment_selector_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.environment_selector = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Prod", "UAT", "QA"])
        self.environment_selector.grid(row=6, column=0, padx=20, pady=(10, 10))

        #row 7,8
        self.auth_entry_label = customtkinter.CTkLabel(self.sidebar_frame, text="Auth Code:", anchor="w")
        self.auth_entry_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.auth_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Auth Code")
        self.auth_entry.grid(row=8, column=0, padx=20, pady=10)

        #row 9
        self.load_button = customtkinter.CTkButton(self.sidebar_frame, text="Load", command=self.load_pressed)
        self.load_button.grid(row=9, column=0, padx=20, pady=10)

        ##product GUIDs Frame

        self.product_guids_frame = customtkinter.CTkFrame(self, width=280, corner_radius=10)
        self.product_guids_frame.grid(row=0, column=1, rowspan=10, padx = (0,10), pady = 10, sticky="nsew")

        self.product_guids_label = customtkinter.CTkLabel(self.product_guids_frame, text="Product Guids:", anchor="w")
        self.product_guids_label.grid(row=0, column=0, padx=20, pady=(10, 0))

        self.product_guids_textbox = customtkinter.CTkTextbox(self.product_guids_frame, width=270,)
        self.product_guids_textbox.grid(row=1, column=0, padx=(20, 0), pady=(20, 0), sticky="nsew")

        self.search_guids_button = customtkinter.CTkButton(self.product_guids_frame, text="Search", command=self.load_pressed)
        self.search_guids_button.grid(row=2, column=0, padx=20, pady=(10, 0))


    def load_pressed(self):
        print("load pressed")
        workflowId, dataowner, environment, auth = save_worfklow_info(
            self.workflow_id.get(),
            self.workflow_dataowner.get(),
            self.environment_selector.get(),
            self.auth_entry.get()
            )
        print(workflowId, dataowner, environment, auth)
        


if __name__ == "__main__":
    app = App()
    app.mainloop()