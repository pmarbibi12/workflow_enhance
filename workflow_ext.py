import customtkinter
import pandas as pd
import CTkTable
from CTkTable import *
import requests
import json
import os
import threading
import concurrent.futures
import time
from CTkTableRowSelector import *


customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"


class OutputFrame(customtkinter.CTkScrollableFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
    
        columns = [["Product ID", "Updated", "Status", "Instance ID", "Version"]]

        self.tree_view = CTkTable(self, row=1 , column=5, values=columns)
        self.tree_view.grid(row=0,column=0)

class SuccessWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Workflow_Ext")
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
        self.title("Workflow_Ext")
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
        self.title("Workflow_Ext")
        self.geometry("400x150+500+500")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)


        self.ok_button = customtkinter.CTkButton(self, text="OK", command=self.destroy)
        self.ok_button.grid(row=2, column=0, pady=(0,20))

class WarningWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Workflow_Ext")
        self.geometry("700x150+500+500")
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1), weight=1)

class UpgradeWindow(customtkinter.CTkToplevel):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title("Workflow_Ext")
        self.geometry("400x150+500+500")
        self.grid_columnconfigure((0,1), weight=1)
        self.grid_rowconfigure((0,1), weight=1)

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
        self.workflow_name = str
        self.env = str
        self.headers = str
        self.guids_array = []
        self.api_thread = None
        self.table_created = False
        self.table_creation_lock = threading.Lock()
        self.upgrade_data = {}
        self.true_num = 0
        self.false_num = 0
        self.table = None
        self.filtered_df = pd.DataFrame()
        self.workflow_versions = []

        # configure window
        self.title("Workflow_Ext")
        self.geometry(f"{1440}x{800}+{100}+{100}")
        # configure grid layout (4x4)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure((0,1), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.create_sidebar_widgets()
        self.create_search_widgets()
        self.create_output_widgets()
        self.create_additional_actions_widgets()
      
    def create_sidebar_widgets(self):

        ## sidebar frame

        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, padx = 10, pady = 10, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

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

        # row 11
        self.wf_name_label = customtkinter.CTkLabel(self.sidebar_frame, text="Workflow Name:")
        self.wf_name_label.grid(row=11, column=0, padx=20, pady=(10, 0))

        # row 12
        self.wf_frame = customtkinter.CTkFrame(self.sidebar_frame, height = 40, border_color="gray", border_width=2)
        self.wf_frame.grid(row=12, column=0, padx=10, pady=(0,15))
        self.wf_frame.grid_columnconfigure(0, weight=1)

        self.wf_name = customtkinter.CTkLabel(self.wf_frame, text="                        ",font=customtkinter.CTkFont(size=14, weight="bold"))
        self.wf_name.grid(row=0, column=0, pady=5, padx=15)

        self.appearance_label = customtkinter.CTkLabel(self.sidebar_frame, text="Theme:")
        self.appearance_label.grid(row=13, column=0, padx=5, pady=(5, 5))

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=14,column=0, pady=(5,15), padx=5)


        ### search Frame
    
    def create_search_widgets(self):
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
        self.product_guids_textbox = customtkinter.CTkTextbox(self.product_guids_frame, width=260)
        self.product_guids_textbox.grid(row=0, column=0, sticky="nsew")
        
        # row 1
        self.search_guids_button = customtkinter.CTkButton(self.product_guids_frame, text="Load Workflow First", command=self.search_clicked, state="disabled")
        self.search_guids_button.grid(row=1, column=0, padx=20, pady=15)

        # row 2
        self.upgrade_button = customtkinter.CTkButton(self.product_guids_frame, text="Search Items First", command=self.start_upgrade, state="disabled")
        self.upgrade_button.grid(row=2, column=0, padx=20, pady=(0,15))

    def create_output_widgets(self):

        ### output Frame
        self.output_frame = customtkinter.CTkFrame(self, width=500, corner_radius=10)
        self.output_frame.grid(row=0, column=2, rowspan=10, pady = 10, sticky="nsew")
        self.output_frame.grid_columnconfigure(0, weight=1)
        self.output_frame.grid_rowconfigure(2, weight=1)
        self.output_frame.grid_rowconfigure((0,1,3), weight=0)

        # ouput frame rows

        self.output_label = customtkinter.CTkLabel(self.output_frame, text="Output:", justify= "left")
        self.output_label.grid(row=0, column=0, padx=20, pady=(10,5))


        self.filter_bar = customtkinter.CTkFrame(self.output_frame,width=500)
        self.filter_bar.grid(row=1,column=0,pady=5)
        self.filter_bar.grid_columnconfigure((0,1,2,3,4), weight=1)
        self.filter_bar.grid_rowconfigure(0,weight=1)

        self.filter_bar.filter_bar_label = customtkinter.CTkLabel(self.filter_bar, text="Apply Filters:")
        self.filter_bar.filter_bar_label.grid(row=0, column=0, padx=10)

        self.filter_bar.product_select = customtkinter.CTkButton(self.filter_bar, text = "Product Select",corner_radius=0, command=self.product_select, state="disabled")
        self.filter_bar.product_select.grid(row=0, column=1, padx=1)

        self.filter_bar.status_select = customtkinter.CTkButton(self.filter_bar, text = "Status Filter",corner_radius=0, command=self.status_select, state="disabled")
        self.filter_bar.status_select.grid(row=0,column=2, padx=1)

        self.filter_bar.version_select = customtkinter.CTkButton(self.filter_bar, text = "Version Filter",corner_radius=0, command=self.version_select, state="disabled")
        self.filter_bar.version_select.grid(row=0,column=3, padx=1)

        self.filter_bar.remove_filters = customtkinter.CTkButton(self.filter_bar, text = "Remove filters",corner_radius=0, text_color="lightgreen", command=self.remove_filters, state="disabled")
        self.filter_bar.remove_filters.grid(row=0,column=4, padx=2)
        

        self.df_frame = OutputFrame(self.output_frame)
        self.df_frame.grid(row=2, column=0, padx =15, pady = (10,15), sticky="nsew")
        self.df_frame.grid_columnconfigure(0, weight = 1)

        self.progress_bar = customtkinter.CTkProgressBar(self.output_frame, height=10, width=500, indeterminate_speed=2)
        self.progress_bar.grid(row=3, column=0, pady=(10,25))
        self.progress_bar.set(0)

    def create_additional_actions_widgets(self):
        ### additional actions

        self.additional_actions_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.additional_actions_frame.grid(row=0, column=3, rowspan=10, padx = 10, pady = 10, sticky="nsew")
        self.additional_actions_frame.grid_columnconfigure(0, weight=1)
        self.additional_actions_frame.grid_rowconfigure(5, weight=1)

        ## additional rows

        self.logo_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Additional Actions", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.csv_file_entry_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Enter Filename:", anchor="w")
        self.csv_file_entry_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.csv_file_entry = customtkinter.CTkEntry(self.additional_actions_frame, placeholder_text="filename.csv")
        self.csv_file_entry.grid(row=2, column=0, pady=(10,0))

        self.row_selector = CTkTableRowSelector(self.df_frame.tree_view)

        # self.output_to_csv_button = customtkinter.CTkButton(self.additional_actions_frame, text="Export to CSV", command=lambda: print(self.row_selector.get()), state="disabled")
        self.output_to_csv_button = customtkinter.CTkButton(self.additional_actions_frame, text="Export to CSV", command=self.overwrite_warning, state="disabled")
        self.output_to_csv_button.grid(row=3, column=0, pady=(20,15))

        self.instance_id_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Instance IDs:", anchor="w")
        self.instance_id_label.grid(row=4, column=0, padx=20, pady=10)

        self.instance_id_textbox = customtkinter.CTkTextbox(self.additional_actions_frame)
        self.instance_id_textbox.grid(row=5, column=0,padx=10, pady=(0,5), sticky="nsew")

        self.export_state_button = customtkinter.CTkButton(self.additional_actions_frame, text="Load Workflow First", command=self.export_state, state="disabled")
        self.export_state_button.grid(row=6, column=0, pady=(10,15))

    def export_state(self):

        try:
            instance_ids = self.instance_id_textbox.get("0.0", "end")
        except Exception as e:
            print(f"Error getting text from instance_id_textbox: {e}")
            instance_ids = ""
        instance_ids_array = [line.strip() for line in instance_ids.split('\n') if line.strip()]

        if len(instance_ids_array) > 0:

            instance_search_url = f"https://{self.env_url}/api/workflow/WorkflowGrain/export/{self.workflowId}/"

            file_names = []
            failed_exports = []

            output_folder = "../../workflow_states"
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            for instance in instance_ids_array:
                response = requests.get(instance_search_url+instance, headers=self.headers)

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
            self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"JSON files saved to '{output_folder}'")
            self.output_window.output_label.grid(row=0, column=0, pady=15)
            self.output_window.output_label2 = customtkinter.CTkLabel(self.output_window, text=f"{len(failed_exports)} failed to export")
            self.output_window.output_label2.grid(row=1, column=0, pady=15)
        else:
            self.output_window = OutputWindow(self)
            self.output_window.grab_set()
            self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"Nothing to export")
            self.output_window.output_label.grid(row=0, column=0, pady=15)

        return None

    def load_clicked(self):
        print("load clicked")
        self.workflowId = self.workflow_id.get()
        self.workflowId = self.workflowId.strip()
        self.dataowner = self.workflow_dataowner.get()
        self.dataowner = self.dataowner.strip()
        self.auth = self.auth_entry.get()
        self.auth = self.auth.strip()
        self.env = self.environment_selector.get()
        self.env_url = self.get_environment_url(self.env)
        self.headers = self.get_headers()

        self.steps_with_names = self.get_status_info()

    def get_environment_url(self,x):
        if x == "Prod":
            return "api.syndigo.com"
        elif x == "UAT":
            return "api.uat.syndigo.com"
        elif x == "QA":
            return "cxhapi-qa.edgenet.com"
        
    def get_status_info(self):

        wf_name_and_statuses = f"https://{self.env_url}/api/workflow/workflowgrain/bydataowner/{self.dataowner}"

        name_response = requests.get(wf_name_and_statuses, headers=self.headers)

        wf_statuses = []
        step_ids = []
        step_desc = []

        if name_response.status_code == 200:
            
            response_json = name_response.json()

            print(len(response_json))

            if len(response_json) == 0:
                self.fail_window = FailWindow(self)
                self.fail_window.grab_set()

                wf_statuses.append("No Statuses")

                self.search_guids_button.configure(state="disabled", text="Load Workflow First")
                self.export_state_button.configure(state="disabled", text="Load Workflow First")
                self.upgrade_button.configure(state="disabled", text="Load Workflow First")

                self.wf_name.configure(text="                        ")
                self.title("Workflow_Ext")
            else:
                step_names = response_json[self.workflowId]
                self.workflow_name = step_names["WorkflowName"]

                self.success_window = SuccessWindow(self)
                self.success_window.grab_set()

                self.search_guids_button.configure(state="normal", text="Search")
                self.export_state_button.configure(state="normal", text="Export State")

                self.wf_name.configure(text=self.workflow_name)
                self.title(f"Workflow_Ext -- {self.workflow_name} ({self.env})")

                for step_id, step_data in step_names.get("StepNames", {}).items():
                    step_ids.append(step_id)
                    step_desc.append(step_data.get("InvariantCultureDescription"))
                self.steps_with_names = {step_id : desc for step_id, desc in zip(step_ids, step_desc)}
        else:
            self.fail_window = FailWindow(self)
            self.fail_window.grab_set()
            wf_statuses.append("No Statuses")
            self.search_guids_button.configure(state="disabled", text="Load Workflow First")
            self.export_state_button.configure(state="disabled", text="Load Workflow First")
            self.wf_name.configure(text="                        ")
            self.title("Workflow_Ext")

        return self.steps_with_names

    def delete_table(self):
        self.df_frame.tree_view.destroy()
        self.init_table()

    def init_table(self):
        columns = [["Product ID", "Updated", "Status", "Instance ID", "Version"]]
        self.df_frame.tree_view = CTkTable(master=self.df_frame, row=1 , column=5, values=columns)
        self.df_frame.tree_view.grid(row=0,column=0)
        
    def search_clicked(self):

        self.table_created = False

        if self.rowNum > 0:
            self.delete_table()
 
        self.guids_array = self.get_guids()

        self.progress_bar.set(0)
        
        self.search_guids_button.configure(state="disabled")

        self.progress_bar.start()
        self.api_thread = threading.Thread(target=self.getStatuses)
        self.api_thread.start()

        return None
    
    def create_table(self, df):

        if not self.table_created:
            self.output_to_csv_button.configure(state="normal")
            df_rows = [df.columns.tolist()] + df.to_numpy().tolist()

            self.rowNum = len(df_rows)

            self.df_frame.tree_view = CTkTable(self.df_frame, row=self.rowNum, column=5, values=df_rows)
            self.df_frame.tree_view.grid(row=0,column=0)

            self.table = self.df_frame.tree_view
            self.row_selector = CTkTableRowSelector(self.table)

            self.search_guids_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.set(1)
            self.upgrade_button.configure(state="normal", text="Upgrade Items in Table")
            self.filter_bar.product_select.configure(state="normal")
            self.filter_bar.status_select.configure(state="normal")
            self.filter_bar.version_select.configure(state="normal")
            self.filter_bar.remove_filters.configure(state="normal")

            self.workflow_versions = df["Version"].unique()

            self.table_created = True

    def getStatuses(self):
        start_time = time.time()
        def fetch_status(product):
            status_search_url = f"https://{self.env_url}/api/workflow/WorkflowGrain/status/{self.workflowId}/{product}"
            response = requests.get(status_search_url, headers=self.headers)
            
            if response.status_code == 200:
                json_response = response.json()
                timestamp_response = json_response["Timestamp"]
                status_response = json_response["Statuses"]
                
                stat_names = [self.steps_with_names.get(status, status) for status in status_response]
                stat_names_str = ", ".join(stat_names)

                return {
                    "Product ID": product,
                    "Updated": timestamp_response,
                    "Status": stat_names_str,
                    "Instance ID": json_response["WorkflowInstanceId"],
                    "Version": json_response["WorkflowVersion"]
                }
            else:
                return {
                    "Product ID": product,
                    "Updated": "Null",
                    "Status": "Null",
                    "Instance ID": "Null",
                    "Version": "Null"
                }

        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(fetch_status, self.guids_array))
        
        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time

        print(f"statuses retrieved in {elapsed_time:.2f} seconds")

        self.workflow_statuses = pd.DataFrame(results)
        self.workflow_versions = self.workflow_statuses["Version"].unique()
        self.after(0, self.create_table(self.workflow_statuses))
         
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

    def overwrite_warning(self):
        filename = self.csv_file_entry.get()

        if not filename:
            filename = "output.csv"
        elif filename[-4:] != ".csv":
            filename += ".csv"
        
        self.warn_window = WarningWindow(self)
        self.warn_window.grab_set()

        self.warn_window.warn_label = customtkinter.CTkLabel(self.warn_window, text=f"Warning! This will overwrite {filename} if it already exists",font=customtkinter.CTkFont(size=14, weight="bold"))
        self.warn_window.warn_label.grid(row=0, column=0, pady=(15,10), padx=20)

        self.warn_window.continue_button = customtkinter.CTkButton(self.warn_window, text="Continue", command=lambda: self.export_to_csv(filename))
        self.warn_window.continue_button.grid(row=0, column=1, pady=(10,5), padx=10)

        self.warn_window.cancel_button = customtkinter.CTkButton(self.warn_window, text="Cancel", command=self.warn_window.destroy)
        self.warn_window.cancel_button.grid(row=1, column=1, pady=(5,10), padx=10)

    def export_to_csv(self, filename):
        
        self.warn_window.destroy()
        
        self.workflow_statuses.to_csv("../../"+filename, index=False)

        self.output_window = OutputWindow(self)
        self.output_window.grab_set()
        self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"CSV file saved as {filename}")
        self.output_window.output_label.grid(row=0, column=0, pady=15)

    def start_upgrade(self):

        self.upgrade_button.configure(state="disabled")
        
        productIds = self.get_guids()

        if self.guids_array != productIds:
            self.search_first_window = customtkinter.CTkToplevel(self)
            self.search_first_window.geometry("400x200")
            self.search_first_window.grid_columnconfigure(0, weight=1)
            self.search_first_window.grid_rowconfigure((0,1), weight=1)
            self.search_first_window.title("Workflow_Ext")
            self.search_first_window.grab_set()

            self.search_first_window.warn_label = customtkinter.CTkLabel(self.search_first_window, text="Product GUIDs have changed. Search to load statuses.")
            self.search_first_window.warn_label.grid(row=0, column=0, pady=(0,5))

            self.search_first_window.ok_button = customtkinter.CTkButton(self.search_first_window, text="Ok", command=self.search_first_window.destroy)
            self.search_first_window.ok_button.grid(row=1, column=0, pady=(5,0))
        else:
            self.progress_bar.set(0)
            self.progress_bar.start()

            upgrade_thread = threading.Thread(target=self.upgrade_items)
            upgrade_thread.start()

    def export_upgrades(self, data, upgrade_window):
        upgrade_window.destroy()

        df = pd.DataFrame(data)
        df.to_csv("../../upgrade_results.csv", index=False)

        self.output_window = OutputWindow(self)
        self.output_window.grab_set()
        self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"Results saved to upgrade_results.csv")
        self.output_window.output_label.grid(row=0, column=0, pady=15)

    def get_guids(self):
        try:
            product_guids = self.product_guids_textbox.get("0.0", "end")
        except Exception as e:
            print(f"Error getting text from product_guids_textbox: {e}")
            product_guids = ""
        guids_array = [line.strip() for line in product_guids.split('\n') if line.strip()]

        return guids_array

    def upgrade_items(self):
        start_time = time.time()  # Record the start time

        if self.filtered_df.empty:
            current_df = self.workflow_statuses
        else:
            current_df = self.filtered_df

        product_ids = current_df["Product ID"]
        instance_ids = current_df["Instance ID"]
        skip = "?skipApplyingStatuses=true"
        upgrade_url = f"https://{self.env_url}/api/workflow/Debug/upgrade/{self.workflowId}/"

        success = []
        self.true_num = 0
        self.false_num = 0

        def process_upgrade(guid):
            instance_index = product_ids.index(guid)  # Get the index for the current GUID
            url = f"{upgrade_url}{instance_ids[instance_index]}/{guid}{skip}"
            response = requests.get(url, headers=self.headers)

            if response.status_code == 200:
                success.append(True)
                self.true_num += 1
            else:
                success.append(False)
                self.false_num += 1

        # Use a ThreadPoolExecutor with a maximum of 20 workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
            executor.map(process_upgrade, product_ids)

        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time

        self.upgrade_data = {
            "Product GUIDs": product_ids,
            "Success": success
        }
        print(f"Upgrade completed in {elapsed_time:.2f} seconds")

        self.after(0, self.upgrade_output)

    def upgrade_output(self):
        self.progress_bar.set(1)
        self.progress_bar.stop()
        self.upgrade_button.configure(state="normal")
        self.upgrade_window = UpgradeWindow(self)
        self.upgrade_window.grab_set()
        self.upgrade_window.output_label = customtkinter.CTkLabel(self.upgrade_window, text=f"{self.true_num} items upgraded")
        self.upgrade_window.output_label.grid(row=0, column=0, padx=5, pady=5)
        self.upgrade_window.output_label2 = customtkinter.CTkLabel(self.upgrade_window, text=f"{self.false_num} items failed to upgrade")
        self.upgrade_window.output_label2.grid(row=1, column=0, padx=5, pady=5)
        self.upgrade_window.ok_button = customtkinter.CTkButton(self.upgrade_window, text="Ok", command = self.upgrade_window.destroy)
        self.upgrade_window.ok_button.grid(row=0, column=1, padx=5, pady=5)
        self.upgrade_window.export_button = customtkinter.CTkButton(self.upgrade_window, text="Export", command =lambda: self.export_upgrades(self.upgrade_data,self.upgrade_window))
        self.upgrade_window.export_button.grid(row=1, column=1, padx=5, pady=5)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        
    def product_select(self):
        self.product_window = customtkinter.CTkToplevel(self)
        self.product_window.geometry("350x550+500+500")
        self.product_window.grid_columnconfigure(0, weight=1)
        self.product_window.grid_rowconfigure(1, weight=1)
        self.product_window.grid_rowconfigure((0,2), weight=0)
        self.product_window.title("Workflow_Ext - Products")
        self.product_window.grab_set()

        self.product_window.products_frame = customtkinter.CTkScrollableFrame(self.product_window, height=500, width=330)
        self.product_window.products_frame.grid(row=1,column=0,padx=15,pady=(5,15))
        self.product_window.products_frame.grid_columnconfigure(0,weight=0)

        if self.filtered_df.empty:
            current_df = self.workflow_statuses
        else:
            current_df = self.filtered_df

        checkboxes = []
        ind = 0
        for i in current_df["Product ID"]:
            self.product_window.products_frame.i = customtkinter.CTkCheckBox(self.product_window.products_frame, text=f"{i}")
            self.product_window.products_frame.i.grid(row=ind, column=0, pady=5, padx=(5,0), sticky="w")
            checkboxes.append(self.product_window.products_frame.i)
            ind += 1
            
        self.product_window.ok_button = customtkinter.CTkButton(self.product_window, text ="Filter", command=lambda: self.filter_products(checkboxes))
        self.product_window.ok_button.grid(row=2, column=0, pady=15)

        self.product_window.select_all = customtkinter.CTkCheckBox(self.product_window, text="Select All", command=lambda: self.select_all(checkboxes))
        self.product_window.select_all.grid(row=0,column=0,pady=(20,5))

    def select_all(self, value_list):
        
        choice = self.product_window.select_all.get()
        print(choice)
        
        x=0
        for i in value_list:
            if choice == 0:
                i.deselect()
            else:
                i.select()
            x += 1
        return None

    def filter_products(self, value_list):

        print("filtering products")
        
        to_filter = []
        for i in value_list:
            if i.get() == 1:
                value = i.cget("text")
                to_filter.append(value)

        if self.filtered_df.empty:
            current_df = self.workflow_statuses
        elif len(value_list) < self.filtered_df.shape[0]:
            current_df = self.filtered_df
        else:
            current_df = self.workflow_statuses

        self.filtered_df = current_df[current_df["Product ID"].isin(to_filter)]

        self.filtered_df.reset_index(drop=True,inplace=True)

        self.table_created = False
        self.table.destroy()
        self.create_table(self.filtered_df)

        return None

    def status_select(self):
        self.product_window = customtkinter.CTkToplevel(self)
        self.product_window.geometry("350x550+500+500")
        self.product_window.grid_columnconfigure(0, weight=1)
        self.product_window.grid_rowconfigure(1, weight=1)
        self.product_window.grid_rowconfigure((0,2), weight=0)
        self.product_window.title("Workflow_Ext - Statuses")
        self.product_window.grab_set()

        self.product_window.products_frame = customtkinter.CTkScrollableFrame(self.product_window, height=500, width=330)
        self.product_window.products_frame.grid(row=1,column=0,padx=15,pady=(5,15))

        statuses = list(self.steps_with_names.values())

        checkboxes = []

        ind=0

        for i in statuses:
            self.product_window.products_frame.i = customtkinter.CTkCheckBox(self.product_window.products_frame, text=f"{i}")
            self.product_window.products_frame.i.grid(row=ind,column=0,pady=5, sticky="w")
            checkboxes.append(self.product_window.products_frame.i)
            ind += 1

        self.product_window.ok_button = customtkinter.CTkButton(self.product_window, text ="Filter", command=lambda: self.filter_status(checkboxes))
        self.product_window.ok_button.grid(row=2, column=0, pady=15)

        self.product_window.select_all = customtkinter.CTkCheckBox(self.product_window, text="Select All", command=lambda: self.select_all(checkboxes))
        self.product_window.select_all.grid(row=0,column=0,pady=(20,5))

    def filter_status(self,value_list):
        print ("filtering statuses")

        to_filter = []
        for i in value_list:
            if i.get() == 1:
                value = i.cget("text")
                to_filter.append(value)
        
        if self.filtered_df.empty:
            current_df = self.workflow_statuses
        else:
            current_df = self.filtered_df
        
        def contains_filter(statuses):
            statuses_list = statuses.split(', ')
            return any(value in statuses_list for value in to_filter)
        

        self.filtered_df = current_df[current_df['Status'].apply(lambda x: contains_filter(x))]
        self.filtered_df.reset_index(drop=True,inplace=True)

        self.table_created = False
        self.table.destroy()
        self.create_table(self.filtered_df)

        return None

    def version_select(self):
        self.product_window = customtkinter.CTkToplevel(self)
        self.product_window.geometry("180x300+500+500")
        self.product_window.grid_columnconfigure(0, weight=1)
        self.product_window.grid_rowconfigure(1, weight=1)
        self.product_window.grid_rowconfigure((0,2), weight=0)
        self.product_window.title("Workflow_Ext - Versions")
        self.product_window.grab_set()

        self.product_window.products_frame = customtkinter.CTkScrollableFrame(self.product_window, height=500, width=330)
        self.product_window.products_frame.grid(row=1,column=0,padx=15,pady=(5,15))

        versions = self.workflow_versions

        checkboxes = []

        ind=0
        
        for i in versions:
            self.product_window.products_frame.i = customtkinter.CTkCheckBox(self.product_window.products_frame, text=f"{i}")
            self.product_window.products_frame.i.grid(row=ind,column=0,pady=5, sticky="w")
            checkboxes.append(self.product_window.products_frame.i)
            ind += 1

        self.product_window.ok_button = customtkinter.CTkButton(self.product_window, text ="Filter", command=lambda: self.filter_version(checkboxes))
        self.product_window.ok_button.grid(row=2, column=0, pady=15)

        self.product_window.select_all = customtkinter.CTkCheckBox(self.product_window, text="Select All", command=lambda: self.select_all(checkboxes))
        self.product_window.select_all.grid(row=0,column=0,pady=(20,5))

    def filter_version(self, value_list):
        print("filtering versions")
        
        to_filter = []
        for i in value_list:
            if i.get() == 1:
                value = int(i.cget("text"))
                to_filter.append(value)

        print(to_filter)
        
        if self.filtered_df.empty:
            current_df = self.workflow_statuses
            print("Using Original DF")
        elif len(to_filter) < len(self.workflow_versions):
            current_df = self.filtered_df
            print("Using filtered_df")
        else:
            current_df = self.workflow_statuses
            print("Using Original DF")

        self.filtered_df = current_df[current_df["Version"].isin(to_filter)]
        self.filtered_df.reset_index(drop=True,inplace=True)
        
        self.workflow_versions = to_filter

        self.table_created = False
        self.table.destroy()
        self.create_table(self.filtered_df)

        return None

    def remove_filters(self):
        self.filtered_df = self.workflow_statuses
        self.table_created = False
        self.table.destroy()
        self.create_table(self.workflow_statuses)


if __name__ == "__main__":
    app = WorkflowEnhance()
    app.mainloop()