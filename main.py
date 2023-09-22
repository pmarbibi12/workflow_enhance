
import tkinter as tk
# import tkinter.messagebox
from tkinter import ttk
import customtkinter
# from functions_ex import *
from pandastable import Table
import pandas as pd
import CTkTable
from CTkTable import *
import logging
import requests
import json
import os


logging.basicConfig(level=logging.ERROR)

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


class OutputFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
    
        columns = [["Product ID", "Updated", "Status", "Instance ID", "Version"]]

        self.tree_view = CTkTable(master=self, row=1 , column=5, values=columns)
        self.tree_view.grid(row=0,column=0)

class SuccessWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("200x100+500+500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label = customtkinter.CTkLabel(self, text="Workflow successfully loaded")
        self.label.grid(row=0, column=0)

        self.ok_button = customtkinter.CTkButton(self, text="OK", command=self.destroy)
        self.ok_button.grid(row=1, column=0, pady=(0,20))

class FailWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("200x150+500+500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.label = customtkinter.CTkLabel(self, text="Check your values and try again")
        self.label.grid(row=0, column=0)

        self.ok_button = customtkinter.CTkButton(self, text="OK", command=self.destroy)
        self.ok_button.grid(row=1, column=0, pady=(0,20))

class OutputWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.geometry("400x150+500+500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


        self.ok_button = customtkinter.CTkButton(self, text="OK", command=self.destroy)
        self.ok_button.grid(row=2, column=0, pady=(0,20))

class WorkflowEnhance(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.workflowId = str
        self.dataowner = str
        self.auth = str
        self.steps_with_names = {}
        self.env_url = str
        self.workflow_statuses = pd.DataFrame()
        self.rowNum = 0

        # configure window
        self.title("Workflow Status Getter")
        self.geometry(f"{1200}x{700}+{200}+{200}")

        self.create_widgets()

    def create_widgets(self):

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
        self.load_button = customtkinter.CTkButton(self.sidebar_frame, text="Load", command=self.load_clicked)
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
        self.search_guids_button = customtkinter.CTkButton(self.product_guids_frame, text="Load Workflow First", command=self.search_clicked, state="disabled")
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

        self.df_frame = OutputFrame(self.output_frame)
        self.df_frame.grid(row=1, column=0, rowspan=8, padx =15, pady = (10,15), sticky="nsew")
        self.df_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = customtkinter.CTkProgressBar(self.output_frame)
        self.progress_bar.grid(row=2, column=0, pady=15)
        self.progress_bar.set(0)

        ### additional actions

        self.additional_actions_frame = customtkinter.CTkFrame(self, corner_radius=10, fg_color="transparent")
        self.additional_actions_frame.grid(row=0, column=3, rowspan=10, padx = 10, sticky="nsew")
        self.additional_actions_frame.grid_columnconfigure(0, weight=1)
        self.additional_actions_frame.grid_rowconfigure(5, weight=2)

        ## additional rows

        self.logo_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Additional Actions", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.csv_file_entry_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Enter Filename:", anchor="w")
        self.csv_file_entry_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.csv_file_entry = customtkinter.CTkEntry(self.additional_actions_frame, placeholder_text="filename.csv")
        self.csv_file_entry.grid(row=2, column=0, pady=(15,0))

        self.output_to_csv_button = customtkinter.CTkButton(self.additional_actions_frame, text="Export to CSV", command=self.export_to_csv)
        self.output_to_csv_button.grid(row=3, column=0, pady=20)

        self.instance_id_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Instance IDs:", anchor="w")
        self.instance_id_label.grid(row=4, column=0, padx=20, pady=(10, 0))

        self.instance_id_textbox = customtkinter.CTkTextbox(self.additional_actions_frame)
        self.instance_id_textbox.grid(row=5, column=0, sticky="nsew")

        self.export_state_button = customtkinter.CTkButton(self.additional_actions_frame, text="Export State", command=self.export_state)
        self.export_state_button.grid(row=6, column=0, pady=20)

    def export_state(self):

        try:
            instance_ids = self.instance_id_textbox.get("0.0", "end")
        except Exception as e:
            print(f"Error getting text from instance_id_textbox: {e}")
            instance_ids = ""
        instance_ids_array = [line.strip() for line in instance_ids.split('\n') if line.strip()]

        headers = self.get_headers()

        instance_search_url = f"https://{self.env_url}/api/workflow/WorkflowGrain/export/{self.workflowId}/"

        file_names = []
        failed_exports = []

        output_folder = "workflow_states"
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        for instance in instance_ids_array:
            response = requests.get(instance_search_url+instance, headers=headers)

            if response.status_code == 200:
                json_response = response.json()
                file_name = os.path.join(output_folder,f"{instance}_workflow_state.json")
                with open(file_name, "w") as json_file:
                    json.dump(json_response, json_file)
                file_names.append(file_name)
            else:
                failed_exports.append(instance)

        if len(failed_exports) > 0:
            failed_path = os.path.join(output_folder,"no_state_found.txt")
            with open(failed_path, "w") as text_file:
                for value in failed_exports:
                    text_file.write(value + "\n")

        self.output_window = OutputWindow(self)
        self.output_window.grab_set()
        self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"JSON files saved to '{output_folder}")
        self.output_window.output_label.grid(row=0, column=0, pady=15)
        self.output_window.output_label2 = customtkinter.CTkLabel(self.output_window, text=f"{len(failed_exports)} failed to export")
        self.output_window.output_label2.grid(row=1, column=0, pady=15)

        return None

    def load_clicked(self):
        print("load clicked")
        self.workflowId = self.workflow_id.get()
        self.workflowId = self.workflowId.strip()
        self.dataowner = self.workflow_dataowner.get()
        self.dataowner = self.dataowner.strip()
        self.auth = self.auth_entry.get()
        self.auth = self.auth.strip()
        env= self.environment_selector.get()
        self.env_url = self.get_environment_url(env)

        self.steps_with_names = self.get_status_info()
        
        # print(self.workflowId, self.dataowner, self.auth, self.env_url)

    def get_environment_url(self,x):
        if x == "Prod":
            return "api.syndigo.com"
        elif x == "UAT":
            return "api.uat.syndigo.com"
        elif x == "QA":
            return "cxhapi-qa.edgenet.com"
        
    def get_status_info(self):

        wf_name_and_statuses = f"https://{self.env_url}/api/workflow/workflowgrain/bydataowner/{self.dataowner}"
        
        headers = self.get_headers()

        name_response = requests.get(wf_name_and_statuses, headers=headers)

        wf_statuses = []
        step_ids = []
        step_desc = []

        if name_response.status_code == 200:
            self.success_window = SuccessWindow(self)
            self.success_window.grab_set()
            self.search_guids_button.configure(state="normal", text="Search")
            response_json = name_response.json()
            step_names = response_json[self.workflowId]
            for step_id, step_data in step_names.get("StepNames", {}).items():
                step_ids.append(step_id)
                step_desc.append(step_data.get("InvariantCultureDescription"))
            self.steps_with_names = {step_id : desc for step_id, desc in zip(step_ids, step_desc)}
        else:
            self.fail_window = FailWindow(self)
            self.fail_window.grab_set()
            wf_statuses.append("No Statuses")

        return self.steps_with_names

    def delete_table(self):
        self.df_frame.tree_view.destroy()
        self.init_table()

    def init_table(self):
        columns = [["Product ID", "Updated", "Status", "Instance ID", "Version"]]
        self.df_frame.tree_view = CTkTable(master=self.df_frame, row=1 , column=5, values=columns)
        self.df_frame.tree_view.grid(row=0,column=0)
    
    def search_clicked(self):

        print("search clicked")
        
        self.progress_bar.start()

        if self.rowNum > 0:
            self.delete_table()


        workflowId = "c0c48edf-2645-4271-b8b6-cfa33d720876"
        dataowner = "c7407733-1be6-452b-82b1-95a89c0cb2a1"
        auth = "EN AkVOZZ4SaRThrEuRm/U8cL6KKAhwbWFyYmliaXT9eVFP6tkBdT1ees/v2QECAAAAEkVOLlJvb3RQZXJtaXNzaW9ucwMxMjYAAA9FTi5Vc2VyRnVsbE5hbWULUGFuIE1hcmJpYmkAAIscXAbqdbcCteYGlP6CJ1TLYqVi3vNx2gUnkVyUYnEM3zMiNKM+CwAmhr2AKW9cUFqw0UcwwBXL2FH87+e76hKPok65AP0Tf9+7P8fPZd/uV1iDH600hSxVf/w8LkFQc1Uh1JXlexAzQEDRXhvLYU9C5UR73ITqWiX+L6mJYoxl"
        
        try:
            product_guids = self.product_guids_textbox.get("0.0", "end")
        except Exception as e:
            print(f"Error getting text from product_guids_textbox: {e}")
            product_guids = ""
        guids_array = [line.strip() for line in product_guids.split('\n') if line.strip()]

        data = self.getStatuses(guids_array)
        self.workflow_statuses = pd.DataFrame(data)
        
        df_rows = self.workflow_statuses.to_numpy().tolist()

        self.rowNum = len(df_rows)

        rownum = 1
        for row in df_rows:
            self.df_frame.tree_view.add_row(index=rownum, values=row)
            rownum += 1

        self.progress_bar.stop()
        self.progress_bar.set(1)

        return None
    
    def statusId_to_statusName(self, step_id):

        if step_id in self.steps_with_names:
            return self.steps_with_names[step_id]
        else:
            return step_id
        
    def getStatuses(self, productGuids):
        
        timeStamp = []
        wf_version = []
        instaceIds = []
        statuses = []

        headers = self.get_headers()

        status_search_url = f"https://{self.env_url}/api/workflow/WorkflowGrain/status/{self.workflowId}/"

        for product in productGuids:
            
            response = requests.get(status_search_url+product, headers=headers)
            
            if response.status_code == 200:
                json_response = response.json()
                timestamp_response = json_response["Timestamp"]
                timeStamp.append(timestamp_response)
                status_response = json_response["Statuses"]
                
                stat_names = []
                
                for status in status_response:
                    name = self.statusId_to_statusName(status)
                    stat_names.append(name)

                statuses.append(stat_names)
                wf_version.append(json_response["WorkflowVersion"])
                instaceIds.append(json_response["WorkflowInstanceId"])
            else:
                timeStamp.append("Null")
                statuses.append("Null")
                wf_version.append("Null")
                instaceIds.append("Null")

        data = {
            "Product ID" : productGuids,
            "Updated" : timeStamp,
            "Status" : statuses,
            "Instance ID": instaceIds,
            "Version" : wf_version
        }

        return data
    
    def get_headers(self):
        return {
            "User-Agent": "PostmanRuntime/y.32.3",
            "Accept": "*/*",
            "Accept-Encoding": "gzip,deflate,br" ,
            "Connection" : "keep-alive",
            "Authorization" : self.auth
        }
    
    def test_var(self):
        print(self.workflowId, self.dataowner, self.auth, self.env)

    def export_to_csv(self):
        filename = self.csv_file_entry.get()
        if not filename:
            filename = "output.csv"
        self.workflow_statuses.to_csv(filename, index=False)
        self.output_window = OutputWindow(self)
        self.output_window.grab_set()
        self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"CSV file saved as {filename}")
        self.output_window.output_label.grid(row=0, column=0, pady=15)



if __name__ == "__main__":
    app = WorkflowEnhance()
    app.mainloop()