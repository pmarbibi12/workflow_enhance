
import tkinter as tk
import tkinter.messagebox
from tkinter import ttk
import customtkinter
from wf_get_status_and_versions import *
from pandastable import Table
import pandas as pd
import CTkTable
from CTkTable import *
import asyncio
import functools




customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

class MyFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

        # add widgets onto the frame...
        # self.label = customtkinter.CTkLabel(self)
        # self.label.grid(row=0, column=0, padx=20)

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title("Workflow Status Getter")
        self.geometry(f"{1200}x{700}+{0}x{0}")

        # configure grid layout (4x4)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure((0,1), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        ## sidebar frame

        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, padx = 10, pady = 10, sticky="nsew")

        # row 0
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Load Workflow", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # row 1,2
        self.workflow_id_label = customtkinter.CTkLabel(self.sidebar_frame, text="Workflow ID:", anchor="w")
        self.workflow_id_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.workflow_id = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Workflow ID")
        self.workflow_id.grid(row=2, column=0, padx=20, pady=10)

        # row 3,4
        self.workflow_dataowner_label = customtkinter.CTkLabel(self.sidebar_frame, text="DataOwner ID:", anchor="w")
        self.workflow_dataowner_label.grid(row=3, column=0, padx=20, pady=(10, 0))
        self.workflow_dataowner = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Environment Specific")
        self.workflow_dataowner.grid(row=4, column=0, padx=20, pady=10)

        # row 5,6
        self.environment_selector_label = customtkinter.CTkLabel(self.sidebar_frame, text="Environment:", anchor="w")
        self.environment_selector_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.environment_selector = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Prod", "UAT", "QA"])
        self.environment_selector.grid(row=6, column=0, padx=20, pady=(10, 10))

        # row 7,8
        self.auth_entry_label = customtkinter.CTkLabel(self.sidebar_frame, text="Auth Code:", anchor="w")
        self.auth_entry_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.auth_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Auth Code")
        self.auth_entry.grid(row=8, column=0, padx=20, pady=10)

        # row 9
        self.load_button = customtkinter.CTkButton(self.sidebar_frame, text="Load", command=self.load_pressed)
        self.load_button.grid(row=9, column=0, padx=20, pady=10)

        ### search Frame

        self.search_frame = customtkinter.CTkFrame(self, width=300, corner_radius=10)
        self.search_frame.grid(row=0, column=1, rowspan=10, padx = (0,10), pady = 10, sticky="nsew")
        self.search_frame.grid_rowconfigure(1, weight=1)
        self.search_frame.grid_rowconfigure(0, weight=0)
        self.search_frame.grid_columnconfigure(0, weight=1)
        
        ## search rows

        # row 0
        self.product_guids_label = customtkinter.CTkLabel(self.search_frame, text="Product GUIDs:", justify= "left")
        self.product_guids_label.grid(row=0, column=0, padx=20, pady=10)
        
        # row 1
        ### search-productguids frame 
        self.product_guids_frame = customtkinter.CTkFrame(self.search_frame, corner_radius=10, fg_color="transparent")
        self.product_guids_frame.grid(row=1, column=0, rowspan=10, padx = 10, sticky="nsew")
        self.product_guids_frame.grid_columnconfigure(0, weight=1)
        self.product_guids_frame.grid_rowconfigure(0, weight=1)
        self.product_guids_frame.grid_rowconfigure(1, weight=0)


        ## search-productguids rows

        # row 0
        self.product_guids_textbox = customtkinter.CTkTextbox(self.product_guids_frame)
        self.product_guids_textbox.grid(row=0, column=0, sticky="nsew")
        
        # row 1
        self.search_guids_button = customtkinter.CTkButton(self.product_guids_frame, text="Search", command=self.update_gui)
        self.search_guids_button.grid(row=1, column=0, padx=20, pady=15)

        ### output Frame
        self.output_frame = customtkinter.CTkFrame(self, width=500, corner_radius=10)
        self.output_frame.grid(row=0, column=2, rowspan=10, padx = (0,10), pady = 10, sticky="nsew")
        self.output_frame.grid_columnconfigure(0, weight = 1)
        self.output_frame.grid_rowconfigure(1, weight = 1)
        self.output_frame.grid_rowconfigure((0,2), weight = 0)


        # ouput frame rows

        self.output_label = customtkinter.CTkLabel(self.output_frame, text="Output:", justify= "left")
        self.output_label.grid(row=0, column=0, padx=20, pady=(10,0))

        self.df_frame = MyFrame(self.output_frame)
        self.df_frame.grid(row=1, column=0, rowspan=8, padx =15, pady = (10,15), sticky="nsew")
        self.df_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = customtkinter.CTkProgressBar(self.output_frame)
        self.progress_bar.grid(row=2, column=0, pady=15)
        self.progress_bar.set(0)

    def update_gui(self):
        self.progress_bar.start()
        asyncio.run(self.search_pressed())

    def load_pressed(self):
        print("load pressed")

    async def search_pressed(self):
        print("search pressed")

        # workflowId = self.workflow_id.get()
        # workflowId = workflowId.strip()
        # dataowner = self.workflow_dataowner.get()
        # dataowner = dataowner.strip()
        # auth = self.auth_entry.get()
        # auth = auth.strip()

        workflowId = "c0c48edf-2645-4271-b8b6-cfa33d720876"
        dataowner = "c7407733-1be6-452b-82b1-95a89c0cb2a1"
        auth = "EN AkVOZZ4SaRThrEuRm/U8cL6KKAhwbWFyYmliaXT9eVFP6tkBdT1ees/v2QECAAAAEkVOLlJvb3RQZXJtaXNzaW9ucwMxMjYAAA9FTi5Vc2VyRnVsbE5hbWULUGFuIE1hcmJpYmkAAIscXAbqdbcCteYGlP6CJ1TLYqVi3vNx2gUnkVyUYnEM3zMiNKM+CwAmhr2AKW9cUFqw0UcwwBXL2FH87+e76hKPok65AP0Tf9+7P8fPZd/uV1iDH600hSxVf/w8LkFQc1Uh1JXlexAzQEDRXhvLYU9C5UR73ITqWiX+L6mJYoxl"
           
        environment= self.environment_selector.get()
        env_url = environment_url(environment)

        product_guids = self.product_guids_textbox.get("0.0", "end")
        guids_array = [line.strip() for line in product_guids.split('\n') if line.strip()]

        steps_with_names = get_statuses(dataowner, env_url, workflowId, auth)

        async with await create_session() as session:
            data = await getStatuses(guids_array, steps_with_names, env_url, workflowId, auth, session)
        workflow_statuses = pd.DataFrame(data)

        columns = [list(workflow_statuses.columns)]
        
        df_rows = workflow_statuses.to_numpy().tolist()

        self.tree_view = CTkTable(master=self.df_frame, row=len(df_rows)+1 , column=len(columns[0]), values=columns)
        # self.tree_view = CTkTable(master=self.df_frame, row=len(value) , column=len(value[0]), values=value)
        self.tree_view.grid(row=0,column=0)
        
        rownum = 1
        for row in df_rows:
            self.tree_view.add_row(index=rownum, values=row)
            rownum += 1

        self.progress_bar.stop()
        self.progress_bar.set(1)

        return None

        print(workflowId, dataowner, environment, auth, env_url)
        print(guids_array)


        


if __name__ == "__main__":
    app = App()
    app.mainloop()