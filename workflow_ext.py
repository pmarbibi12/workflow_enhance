import customtkinter
import pandas as pd
import requests
import json
import os
import threading
import concurrent.futures
import time
from pandastable import Table, config
from CTkMessagebox import CTkMessagebox
from tkinter import *


customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("dark-blue")  # Themes: "blue" (standard), "green", "dark-blue"

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

class ProductSearchWindow(customtkinter.CTkToplevel):
    def __init__(self):
        super().__init__()
        self.title("Workflow_Ext - Product Search")
        self.geometry("1200x800+120+120")
        self.grid_columnconfigure((1), weight=1)
        self.grid_rowconfigure((0), weight=1)

        self.steps = app.steps_with_names
        self.auth = app.auth
        self.dataowner = app.dataowner
        self.checkboxes = []
        self.workflowId = app.workflowId
        self.workflowName = app.workflow_name
        self.headers = {
            "Content-Type":"application/json", 
            "Cache-Control": "no-cache", 
            "User-Agent": "PostmanRuntime/y.32.3", 
            "Accept": "*/*", 
            "Accept-Encoding": 
            "gzip,deflate,br" , 
            "Connection" : "keep-alive",
            "Authorization": self.auth
            }
        self.num_results= 0
        self.row_index= 0
        self.selected_statuses = []
        self.selected_attributes = []
        self.exists_attribute = []
        self.results_df = pd.DataFrame()
        self.has_table = False
        self.upgrade_thread = None
        self.stop_event = threading.Event()
        self.progress_bar = None

        self.create_filter_section()
        # self.add_status_select()
        self.create_output_frame()
        # self.grab_set()    

    def create_filter_section(self):
        self.filter_bar = customtkinter.CTkFrame(self)
        self.filter_bar.grid(row=0,column=0, padx=15,pady=(15,10), stick="nsew")
        self.filter_bar.grid_rowconfigure(3,weight=1)

        self.wf_frame = customtkinter.CTkFrame(self.filter_bar, height = 40, border_color="gray", border_width=2)
        self.wf_frame.grid(row=0, column=0, padx=10, pady=10,sticky="nsew")
        self.wf_frame.grid_columnconfigure(0, weight=1)

        self.wf_name = customtkinter.CTkLabel(self.wf_frame, text=self.workflowName,font=customtkinter.CTkFont(size=14, weight="bold"))
        self.wf_name.grid(row=0, column=0, pady=5, padx=15)

        self.filter_select_label = customtkinter.CTkLabel(self.filter_bar, text="Select Filters:")
        self.filter_select_label.grid(row=1, column=0, padx=10, pady=(8,0))

        self.filter_select = customtkinter.CTkFrame(self.filter_bar)
        self.filter_select.grid(row=2,column=0, padx=10,pady=(5,10), sticky="ew")
        self.filter_select.grid_columnconfigure(0,weight=1)

        self.status_checkbox = customtkinter.CTkButton(self.filter_select, text="Workflow Status", command=self.add_status_select)
        self.status_checkbox.grid(row=0,column=0,pady=5)

        self.attribute_checkbox = customtkinter.CTkButton(self.filter_select, text="Identifier by Value(s)", command=self.add_identifier_search_by_value)
        self.attribute_checkbox.grid(row=1,column=0,pady=5)

        self.attribute_contains_checkbox = customtkinter.CTkButton(self.filter_select, text="Contains Identifier", command=self.add_identifier_contains)
        self.attribute_contains_checkbox.grid(row=2,column=0,pady=5)

        self.filter_box = customtkinter.CTkScrollableFrame(self.filter_bar)
        self.filter_box.grid(row=3, column=0, padx=10, pady=5, sticky="nsew")
        self.filter_box.grid_columnconfigure(0, weight=1)

        self.search_button = customtkinter.CTkButton(self.filter_bar, text="Search", command= self.search_products)
        self.search_button.grid(row=4, column=0, padx=10, pady=10, sticky="nsew")
   
    def add_status_select(self):
        to_filter = []
        status_ids = []

        def close_window():
            self.selected_statuses = [value for value in self.selected_statuses if value not in status_ids]
            self.status_select_frame.destroy()

        def save_values(checkboxes): 
            for i in checkboxes:
                if i.get() == 1:
                    value = i.cget("text")
                    to_filter.append(value)
            for key, value in self.steps.items():
                if value in to_filter and key not in self.selected_statuses:
                    status_ids.append(key)
                    self.selected_statuses.append(key)
            self.save_button.configure(state="disabled")
            ok_pressed = CTkMessagebox(title="Workflow_ext", message="Choices Saved", icon="check", option_1="Ok")
            response = ok_pressed.get()
            if response== "Ok":
                ok_pressed.destroy()


        self.status_select_frame = customtkinter.CTkFrame(self.filter_box)
        self.status_select_frame.grid(row=self.row_index, column=0, padx=5, pady=2)
        self.status_select_frame.grid_columnconfigure(0,weight=1)

        self.label_frame = customtkinter.CTkFrame(self.status_select_frame, fg_color="transparent")
        self.label_frame.grid(row=0,column=0, sticky="ew")
        self.label_frame.grid_columnconfigure(1,weight=1)

        self.status_label = customtkinter.CTkLabel(self.label_frame, text="Select Statuses: ")
        self.status_label.grid(row=0,column=0, padx=10,pady=(8,0), sticky="w")

        self.close_button = customtkinter.CTkButton(self.label_frame, text="X", command=lambda: close_window(), width=15,height=15, anchor="e")
        self.close_button.grid(row=0, column=2, padx=5,pady=2, sticky="e")

        self.status_select = customtkinter.CTkScrollableFrame(self.status_select_frame)
        self.status_select.grid(row=1,column=0, padx=10,pady=(5,10))
        self.status_select.grid_columnconfigure(0, weight=1)

        self.save_button = customtkinter.CTkButton(self.status_select_frame, text="Save Choices", command=lambda: save_values(self.checkboxes))
        self.save_button.grid(row=2, column=0, pady=(0,10), padx=10, sticky="ew")

        self.row_index += 1
        self.getStatuses(self.status_select)
    
    def create_output_frame(self):
        
        self.results_frame = customtkinter.CTkFrame(self,fg_color="transparent")
        self.results_frame.grid(row=0,column=1, sticky="nsew")
        self.results_frame.grid_columnconfigure(0, weight=1)
        self.results_frame.grid_rowconfigure(0, weight=1)
        
        self.output_frame = customtkinter.CTkScrollableFrame(self.results_frame)
        self.output_frame.grid(row=0, column=0, padx=(0,10), pady=(15,10), sticky= "nsew")

        self.actions_frame = customtkinter.CTkFrame(self.results_frame)
        self.actions_frame.grid(row=1, column=0, padx=(0,10), pady=(0,10))
        self.actions_frame.grid_rowconfigure(0, weight=1)
        self.actions_frame.grid_columnconfigure((0,1,2,3,4,5), weight=1)
        
        self.filename_label = customtkinter.CTkLabel(self.actions_frame, text="Filename:", anchor="e")
        self.filename_label.grid(row=0, column=0, padx=(10,0), pady=10, sticky="e")

        self.export_filename_entry = customtkinter.CTkEntry(self.actions_frame, width=100)
        self.export_filename_entry.grid(row=0, column=1, padx=(2,2), pady=10)
        self.export_filename_entry.insert(0,"output.csv")

        self.export_to_csv_button = customtkinter.CTkButton(self.actions_frame, text="Export to CSV", state="disabled",
            command=lambda: app.export_to_csv(self.export_filename_entry.get(), self.results_df))
        self.export_to_csv_button.grid(row=0, column=2, padx=(3,10), pady=10)

        self.multiplyer_label = customtkinter.CTkLabel(self.actions_frame, text="Multiplier:")
        self.multiplyer_label.grid(row=0,column=3,padx=(10,0), pady=10, sticky="e")

        self.multiplyer_entry = customtkinter.CTkEntry(self.actions_frame, width=40)
        self.multiplyer_entry.grid(row=0,column=4,padx=(2,0),pady=10)
        self.multiplyer_entry.insert(0,"20")

        self.upgrade_button = customtkinter.CTkButton(self.actions_frame, text="Upgrade Items", state="disabled",
            command=self.start_upgrade)
        self.upgrade_button.grid(row=0, column=5, padx=5, pady=10)

        self.restart_button = customtkinter.CTkButton(self.actions_frame, text="Restart Items", state="disabled",
            command=self.start_restart)
        self.restart_button.grid(row=0, column=6, padx=(0,10), pady=10)

        self.loading_frame = customtkinter.CTkFrame(self.results_frame)
        self.loading_frame.grid(row=2, column=0, padx=(0,10), pady=(0,10), sticky="ew")
        self.loading_frame.grid_columnconfigure(0, weight=1)

        self.progress_bar = customtkinter.CTkProgressBar(self.loading_frame)
        self.progress_bar.grid(row=0, column=0, padx=20, pady=10, sticky="ew")
        self.progress_bar.set(0)

    def getStatuses(self, window):
        statuses = list(self.steps.values())
        self.checkboxes = []

        ind=0

        for i in statuses:
            self.status_select.i = customtkinter.CTkCheckBox(window, text=f"{i}")
            self.status_select.i.grid(row=ind,column=0,pady=5, sticky="w")
            self.checkboxes.append(self.status_select.i)
            ind += 1
    
    def search_products(self):
        false= "false"
        body = {
                "TargetPartyId": "47f66d9f-9429-48ad-8f2a-267dcd67a346",
                "OrderBy": "0994d0f8-35e7-4a6d-9cd9-2ae97cd8b993",
                "AttributeFilterOperator": "And",
                "WorkflowFilters": [
                    {
                        "WorkflowId": self.workflowId,
                        "Statuses": self.selected_statuses
                    }
                ],
                "AttributeExistsFilters": self.exists_attribute,
                "AttributeFilters": self.selected_attributes,
                "Archived": false,
                "DataOwner": self.dataowner,
                "Language": "en-US"
            }

        api_url = "https://api.syndigo.com/ui/product?includeMetadata=false&includeWorkflowData=true&skip=0&take=1"
        response = requests.post(api_url, data=json.dumps(body), headers=self.headers)
        # print(json.dumps(body))
        if response.status_code == 200:
            print("200 OK")
            json_response= response.json()
            self.num_results= json_response["TotalHitCount"]
            print(self.num_results)
            ok_pressed = CTkMessagebox(title="Workflow_ext", message=f"{self.num_results} results returned. Do you want to continue loading the results? (5k Max)", icon="warning", option_1="Yes", option_2="No")
            response = ok_pressed.get()
            if response== "Yes":
                self.search_button.configure(state="disabled")
                self.progress_bar.set(0)
                self.progress_bar.start()
                load_results_thread = threading.Thread(target=self.load_results)
                load_results_thread.start()
                ok_pressed.destroy()
            else:
                ok_pressed.destroy()

        else:
            ok_pressed = CTkMessagebox(title="Workflow_ext", message=f"No results returned!", icon="cancel", option_1="OK")
            response = ok_pressed.get()
            if response== "OK":
                ok_pressed.destroy()
        
    def load_results(self):
        results_list = []
        false= "false"
        body = {
                "TargetPartyId": "47f66d9f-9429-48ad-8f2a-267dcd67a346",
                "OrderBy": "0994d0f8-35e7-4a6d-9cd9-2ae97cd8b993",
                "AttributeFilterOperator": "And",
                "WorkflowFilters": [
                    {
                        "WorkflowId": self.workflowId,
                        "Statuses": self.selected_statuses
                    }
                ],
                "AttributeExistsFilters": self.exists_attribute,
                "AttributeFilters": self.selected_attributes,
                "Archived": false,
                "DataOwner": self.dataowner,
                "Language": "en-US"
            }
        api_url = "https://api.syndigo.com/ui/product?includeMetadata=false&includeWorkflowData=true"
        skip = f"&skip=0&take={self.num_results}"
        response = requests.post(api_url+skip, data=json.dumps(body), headers=self.headers)
        json_response = response.json()
        results =json_response["Results"]
        for result in results:
            workflowData = result["WorkflowStatusData"]

            
            correct_wf = {}
            for i in workflowData:
                if i["WorkflowDefinitionId"] == self.workflowId:
                    correct_wf = i
            components = result["Components"][0]["AttributeValues"]["en-US"]
            status_response = correct_wf["Statuses"]
            stat_names = [self.steps.get(status, status) for status in status_response]
            stat_names_str = ", ".join(stat_names)
            gtin = str
            for  x in components:
                if x["AttributeId"]=="0994d0f8-35e7-4a6d-9cd9-2ae97cd8b993":
                    gtin = x["Value"]

            dict = {
                "GTIN": gtin,
                "Product ID": result["id"],
                "Status": stat_names_str,
                "Instance ID": correct_wf["WorkflowInstanceId"],
                "Version": correct_wf["WorkflowVersion"]
            }

            results_list.append(dict)
        df = pd.DataFrame(results_list)
        self.results_df = df
        # print(df)
        self.after(0, self.create_table(df))

    def add_identifier_search_by_value(self):
        to_filter= []
       
        def close_window():
            print("clicked close")
            self.selected_attributes = [attr for attr in self.selected_attributes if attr not in to_filter]
            self.identifier_search_frame.destroy()

        def save_values():
            attribute_id = self.identifier_entry.get().strip()
            values = self.value_entry.get("0.0", "end")
            values_array = [line.strip() for line in values.split('\n') if line.strip()]
            
            value_dict = {
                "AttributeId": attribute_id,
                "Values": values_array
            }
            self.selected_attributes.append(value_dict)
            to_filter.append(value_dict)
            self.save_values_button.configure(state="disabled")
            ok_pressed = CTkMessagebox(title="Workflow_ext", message="Values Saved", icon="check", option_1="Ok")
            response = ok_pressed.get()
            if response== "Ok":
                ok_pressed.destroy()

        self.identifier_search_frame = customtkinter.CTkFrame(self.filter_box)
        self.identifier_search_frame.grid(row=self.row_index, padx=5, pady=2, sticky="nsew")
        self.identifier_search_frame.grid_columnconfigure(0,weight=1)
        
        self.label_frame = customtkinter.CTkFrame(self.identifier_search_frame, fg_color="transparent")
        self.label_frame.grid(row=0, column=0, sticky="ew")
        self.label_frame.grid_columnconfigure(1, weight=1)

        self.identifier_label = customtkinter.CTkLabel(self.label_frame, text="Identifier GUID:")
        self.identifier_label.grid(row=0,column=0, padx=10,pady=(8,0), sticky="w")

        self.close_button = customtkinter.CTkButton(self.label_frame, text="X", command=lambda: close_window(), width=15,height=15, anchor="e")
        self.close_button.grid(row=0, column=2, padx=5, pady=2, sticky="e")

        self.identifier_entry = customtkinter.CTkEntry(self.identifier_search_frame)
        self.identifier_entry.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.values_label = customtkinter.CTkLabel(self.identifier_search_frame, text="Values:")
        self.values_label.grid(row=2, column=0, padx=5, pady=2, sticky="we")

        self.value_entry = customtkinter.CTkTextbox(self.identifier_search_frame)
        self.value_entry.grid(row=3, column=0, padx=10, pady=(2,10))

        self.save_values_button = customtkinter.CTkButton(self.identifier_search_frame, text="Save Values", command=lambda: save_values())
        self.save_values_button.grid(row=4, column=0, padx=10, pady=(5,10), sticky="nsew")

        self.row_index += 1

    def add_identifier_contains(self):
        to_filter=[]

        def close_window():
            self.exists_attribute = [attr for attr in self.exists_attribute if attr not in to_filter]
            self.identifier_contains_frame.destroy()

        def switch():
            on = self.contains_switch.get()
            if on==1:
                self.contains_switch.configure(text="Contains")
            elif on==0:
                self.contains_switch.configure(text="Does Not Contain")

        def save_values():
            attribute_id = self.identifier_entry.get()
            if self.contains_switch.get() == 1:
                true_false = "true"
            else:
                true_false = "false"
            value_dict = {
                "AttributeId": attribute_id,
                "Exists": true_false
            }
            self.exists_attribute.append(value_dict)
            to_filter.append(value_dict)
            self.save_values_button.configure(state="disabled")
            ok_pressed = CTkMessagebox(title="Workflow_ext", message="Filter Saved", icon="check", option_1="Ok")
            response = ok_pressed.get()
            if response== "Ok":
                ok_pressed.destroy()

        self.identifier_contains_frame = customtkinter.CTkFrame(self.filter_box)
        self.identifier_contains_frame.grid(row=self.row_index, padx=5, pady=2, sticky="nsew")
        self.identifier_contains_frame.grid_columnconfigure(0,weight=1) 

        self.label_frame = customtkinter.CTkFrame(self.identifier_contains_frame, fg_color="transparent")
        self.label_frame.grid(row=0, column=0, sticky="ew")
        self.label_frame.grid_columnconfigure(1, weight=1)

        self.identifier_label = customtkinter.CTkLabel(self.label_frame, text="Identifier GUID:")
        self.identifier_label.grid(row=0,column=0, padx=10,pady=(8,0), sticky="w")

        self.close_button = customtkinter.CTkButton(self.label_frame, text="X", command=lambda: close_window(), width=15,height=15, anchor="e")
        self.close_button.grid(row=0, column=2, padx=5, pady=2, sticky="e")

        self.identifier_entry = customtkinter.CTkEntry(self.identifier_contains_frame)
        self.identifier_entry.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        self.contains_switch = customtkinter.CTkSwitch(self.identifier_contains_frame, text="Contains", command=lambda: switch())
        self.contains_switch.grid(row=2, column=0, padx=10, pady=2)
        self.contains_switch.select()

        self.save_values_button = customtkinter.CTkButton(self.identifier_contains_frame, text="Save Values", command=lambda: save_values())
        self.save_values_button.grid(row=3, column=0, padx=10, pady=(5,10), sticky="nsew")

        self.row_index += 1
        None

    def create_table(self,df):

        if self.has_table == True:
            self.output_table.remove()
            self.output_frame = customtkinter.CTkScrollableFrame(self.results_frame)
            self.output_frame.grid(row=0, column=0, padx=(0,10), pady=(15,10), sticky= "nsew")
        self.output_table = Table(parent=self.output_frame ,dataframe=df, showtoolbar=False, showstatusbar=True, height=600)
        self.output_table.boxoutlinecolor="black"
        self.output_table.textcolor = 'white'
        self.output_table.editable=False
        self.output_table.rowselectedcolor="#4e57c1"
        self.output_table.colselectedcolor="#4e57c1"
        options = {'fontsize':10,'cellbackgr': 'gray' }
        config.apply_options(options,self.output_table)
        self.output_table.show()
        self.search_button.configure(state="normal")
        self.has_table = True

        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.export_to_csv_button.configure(state="normal")
        self.upgrade_button.configure(state="normal")
        self.restart_button.configure(state="normal")
        
    def start_upgrade(self):
        self.progress_bar.set(0)
        self.progress_bar.start()
        self.stop_event.clear()
        self.upgrade_thread = threading.Thread(target=lambda: app.upgrade_items(int(self.multiplyer_entry.get()), self.results_df))
        self.upgrade_thread.start()

    def stop_progress_bar(self):
        print("made it here")
        self.stop_event.set()
        ok_pressed = CTkMessagebox(title="Workflow_ext", message="Action Complete", icon="check", option_1="Ok")
        response = ok_pressed.get()
        if response== "Ok":
            self.progress_bar.stop()
            self.progress_bar.set(1)
            ok_pressed.destroy()

    def start_restart(self):
        self.progress_bar.set(0)
        self.progress_bar.start()
        self.stop_event.clear()
        self.restart_thread = threading.Thread(target=lambda: app.restart_items(int(self.multiplyer_entry.get()), self.results_df))
        self.restart_thread.start()

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
        self.table_present = False
        self.upgrade_data = {}
        self.restart_data = {}
        self.true_num = 0
        self.false_num = 0
        self.table = None
        self.filtered_df = pd.DataFrame()
        self.workflow_versions = []
        self.pt = None
        self.workflow_values = []
        self.saved_workflows = []
        self.elapsed_time = None
        self.num_items = int
        self.product_search_window = None

        # configure window
        self.title("Workflow_Ext")
        self.geometry(f"{1440}x{800}+{100}+{100}")
        # configure grid layout (4x4)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure((0,1), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.create_sidebar_widgets()
        self.load_saved_workflows()
        self.create_search_widgets()
        self.create_output_widgets()
        self.create_additional_actions_widgets()
      
    def create_sidebar_widgets(self):

        ## sidebar frame

        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=10)
        self.sidebar_frame.grid(row=0, column=0, rowspan=10, padx = 10, pady = 10, sticky="nsew")
        self.sidebar_frame.grid_columnconfigure(0, weight=1)
        self.sidebar_frame.grid_rowconfigure(13, weight=1)

        # row 0
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Load Workflow", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # row 1,2
        self.workflow_id_label = customtkinter.CTkLabel(self.sidebar_frame, text="Workflow ID:", anchor="w")
        self.workflow_id_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.workflow_id = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Workflow ID")
        self.workflow_id.grid(row=2, column=0, padx=20, pady=(8,10))

        # row 3,4
        self.workflow_dataowner_label = customtkinter.CTkLabel(self.sidebar_frame, text="DataOwner ID:", anchor="w")
        self.workflow_dataowner_label.grid(row=3, column=0, padx=20, pady=(10, 0))
        self.workflow_dataowner = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Environment Specific")
        self.workflow_dataowner.grid(row=4, column=0, padx=20, pady=(8,10))

        # row 5,6
        self.environment_selector_label = customtkinter.CTkLabel(self.sidebar_frame, text="Environment:", anchor="w")
        self.environment_selector_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.environment_selector = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Prod", "UAT", "QA"])
        self.environment_selector.grid(row=6, column=0, padx=20, pady=(8,10))

        # row 7,8
        self.auth_entry_label = customtkinter.CTkLabel(self.sidebar_frame, text="Auth Code:", anchor="w")
        self.auth_entry_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.auth_entry = customtkinter.CTkEntry(self.sidebar_frame, placeholder_text="Auth Code")
        self.auth_entry.grid(row=8, column=0, padx=20, pady=(8,10))

        # row 9
        self.load_button = customtkinter.CTkButton(self.sidebar_frame, text="Load", command=self.load_clicked)
        self.load_button.grid(row=9, column=0, padx=20, pady=10)

        # row 10
        self.save_button = customtkinter.CTkButton(self.sidebar_frame, text="Save Workflow", command=self.save_workflow, state="disabled")
        self.save_button.grid(row=10, column=0, padx=20, pady=10)

        self.workflow_selector = customtkinter.CTkOptionMenu(self.sidebar_frame,  command=self.load_workflow)
        self.workflow_selector.grid(row=11, column=0, padx=20, pady=10)

        self.product_search_button = customtkinter.CTkButton(self.sidebar_frame, text="Product Search", command=self.open_product_search, state="disabled")
        self.product_search_button.grid(row=12, column=0, padx=20, pady= 10)

        # row 11
        self.wf_name_label = customtkinter.CTkLabel(self.sidebar_frame, text="Workflow Name:")
        self.wf_name_label.grid(row=14, column=0, padx=20, pady=(10, 0))

        # row 12
        self.wf_frame = customtkinter.CTkFrame(self.sidebar_frame, height = 40, border_color="gray", border_width=2)
        self.wf_frame.grid(row=15, column=0, padx=10, pady=(0,15))
        self.wf_frame.grid_columnconfigure(0, weight=1)

        self.wf_name = customtkinter.CTkLabel(self.wf_frame, text="                        ",font=customtkinter.CTkFont(size=14, weight="bold"))
        self.wf_name.grid(row=0, column=0, pady=5, padx=15)

        self.appearance_label = customtkinter.CTkLabel(self.sidebar_frame, text="Theme:")
        self.appearance_label.grid(row=16, column=0, padx=5, pady=(5, 5))

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Dark", "Light", "System"], command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=17,column=0, pady=(5,15), padx=5)


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
        self.product_guids_textbox = customtkinter.CTkTextbox(self.product_guids_frame, width=270)
        self.product_guids_textbox.grid(row=0, column=0, sticky="nsew")
        
        # row 1

        self.search_frame = customtkinter.CTkFrame(self.product_guids_frame)
        self.search_frame.grid(row=1, column=0)
        self.search_frame.grid_columnconfigure((0,1), weight=1)

        self.search_guids_button = customtkinter.CTkButton(self.search_frame, text="Load Workflow First", command=self.search_clicked, state="disabled")
        self.search_guids_button.grid(row=0, column=0, padx=20, pady=15)

        self.search_entry = customtkinter.CTkEntry(self.search_frame, width=40)
        self.search_entry.grid(row=0, column=1,padx=5)
        self.search_entry.insert(0,20)

        # row 2
        
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
        self.filter_bar.grid(row=1,column=0,pady=5, padx=10)
        self.filter_bar.grid_columnconfigure((0,1,2,3,4), weight=1)
        self.filter_bar.grid_rowconfigure(0,weight=1)

        self.filter_bar.filter_bar_label = customtkinter.CTkLabel(self.filter_bar, text="Apply Filters:")
        self.filter_bar.filter_bar_label.grid(row=0, column=0, padx=15)

        self.filter_bar.product_select = customtkinter.CTkButton(self.filter_bar, text = "Product Select",corner_radius=0, command=self.product_select, state="disabled")
        self.filter_bar.product_select.grid(row=0, column=1, padx=1)

        self.filter_bar.status_select = customtkinter.CTkButton(self.filter_bar, text = "Status Filter",corner_radius=0, command=self.status_select, state="disabled")
        self.filter_bar.status_select.grid(row=0,column=2, padx=1)

        self.filter_bar.version_select = customtkinter.CTkButton(self.filter_bar, text = "Version Filter",corner_radius=0, command=self.version_select, state="disabled")
        self.filter_bar.version_select.grid(row=0,column=3, padx=1)

        self.filter_bar.remove_filters = customtkinter.CTkButton(self.filter_bar, text = "Remove filters",corner_radius=0, text_color="lightgreen", command=self.remove_filters, state="disabled")
        self.filter_bar.remove_filters.grid(row=0,column=4, padx=2)
        

        self.df_frame = customtkinter.CTkScrollableFrame(self.output_frame)
        self.df_frame.grid(row=2, column=0, padx =15, pady = (10,15), sticky="nsew")
        # self.df_frame.grid_columnconfigure(0, weight=1)
        # # self.df_frame.grid_columnconfigure(0, weight=0)
        # self.df_frame.grid_rowconfigure(0,weight=1)

        self.progress_bar = customtkinter.CTkProgressBar(self.output_frame, height=10, width=500, indeterminate_speed=2)
        self.progress_bar.grid(row=3, column=0, pady=(5,0))
        self.progress_bar.set(0)

        self.progress_bar_label = customtkinter.CTkLabel(self.output_frame, text="", text_color="lightgreen", font=customtkinter.CTkFont(size=10),fg_color="transparent")
        self.progress_bar_label.grid(row=4,column=0, pady=(0,5))

    def create_additional_actions_widgets(self):
        ### additional actions

        self.additional_actions_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.additional_actions_frame.grid(row=0, column=3, rowspan=10, padx = 10, pady = 10, sticky="nsew")
        self.additional_actions_frame.grid_columnconfigure(0, weight=1)
        self.additional_actions_frame.grid_rowconfigure(7, weight=1)

        ## additional rows

        self.logo_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Additional Actions", font=customtkinter.CTkFont(size=18, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.csv_file_entry_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Enter Filename:", anchor="w")
        self.csv_file_entry_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.csv_file_entry = customtkinter.CTkEntry(self.additional_actions_frame, placeholder_text="filename.csv")
        self.csv_file_entry.grid(row=2, column=0, pady=(10,0))

        self.output_to_csv_button = customtkinter.CTkButton(self.additional_actions_frame, text="Export to CSV", command=self.overwrite_warning, state="disabled")
        self.output_to_csv_button.grid(row=3, column=0, pady=(20,15))

        self.upgrade_button = customtkinter.CTkButton(self.additional_actions_frame, text="Search Items First", command=self.start_upgrade, state="disabled")
        self.upgrade_button.grid(row=4, column=0, padx=20, pady=(0,15))

        self.restart_button = customtkinter.CTkButton(self.additional_actions_frame, text="Search Items First", command=self.start_restart, state="disabled")
        self.restart_button.grid(row=5, column=0, padx=20, pady=(0,15))

        self.instance_id_label = customtkinter.CTkLabel(self.additional_actions_frame, text="Instance IDs:", anchor="w")
        self.instance_id_label.grid(row=6, column=0, padx=20, pady=10)

        self.instance_id_textbox = customtkinter.CTkTextbox(self.additional_actions_frame)
        self.instance_id_textbox.grid(row=7, column=0,padx=10, pady=(0,5), sticky="nsew")

        self.export_state_button = customtkinter.CTkButton(self.additional_actions_frame, text="Load Workflow First", command=self.export_state, state="disabled")
        self.export_state_button.grid(row=8, column=0, pady=(10,15))

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

            if len(response_json) == 0:
                self.fail_window = FailWindow(self)
                self.fail_window.grab_set()

                wf_statuses.append("No Statuses")

                self.search_guids_button.configure(state="disabled", text="Load Workflow First")
                self.export_state_button.configure(state="disabled", text="Load Workflow First")
                self.upgrade_button.configure(state="disabled", text="Load Workflow First")
                self.save_button.configure(state="disabled")
                self.product_search_button.configure(state="disabled")

                self.wf_name.configure(text="                        ")
                self.title("Workflow_Ext")
            else:
                step_names = response_json[self.workflowId]
                self.workflow_name = step_names["WorkflowName"]
                self.workflow_values = [f"{self.workflow_name} ({self.env})",self.workflowId,self.dataowner,self.env]

                self.success_window = SuccessWindow(self)
                self.success_window.grab_set()

                self.search_guids_button.configure(state="normal", text="Search")
                self.export_state_button.configure(state="normal", text="Export State")
                self.save_button.configure(state="normal")
                self.product_search_button.configure(state="normal")

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

        # if self.rowNum > 0:
        #     self.delete_table()
 
        self.guids_array = self.get_guids()

        self.progress_bar.set(0)
        
        self.search_guids_button.configure(state="disabled")

        workers = int(self.search_entry.get())
        self.progress_bar_label.configure(text=f"Searching {len(self.guids_array)} items with {workers} workers.")

        self.progress_bar.start()
        self.api_thread = threading.Thread(target=self.getStatuses)
        self.api_thread.start()

        return None
    
    def create_table(self, df):

        if not self.table_created:
            self.output_to_csv_button.configure(state="normal")
            df_rows = [df.columns.tolist()] + df.to_numpy().tolist()

            self.rowNum = len(df_rows)

            if self.table_present == True:
                self.pt.remove()
                self.df_frame = customtkinter.CTkScrollableFrame(self.output_frame)
                self.df_frame.grid(row=2, column=0, padx =15, pady = (10,15), sticky="nsew")
            
            self.df_frame.tree_view = self.pt = Table(parent=self.df_frame, dataframe=df, showtoolbar=False, showstatusbar=True, height=550)
            self.df_frame.tree_view.grid(row=0,column=0,sticky="nsew")
            self.pt.boxoutlinecolor="black"
            self.pt.textcolor = 'white'
            self.pt.editable=False
            self.pt.rowselectedcolor="#4e57c1"
            self.pt.colselectedcolor="#4e57c1"
            options = {'fontsize':10,'cellbackgr': 'gray' }
            config.apply_options(options,self.pt)
            self.pt.show()
            
            self.search_guids_button.configure(state="normal")
            self.progress_bar.stop()
            self.progress_bar.set(1)
            self.upgrade_button.configure(state="normal", text="Upgrade Items")
            self.restart_button.configure(state="normal", text="Restart Items")
            self.filter_bar.product_select.configure(state="normal")
            self.filter_bar.status_select.configure(state="normal")
            self.filter_bar.version_select.configure(state="normal")
            self.filter_bar.remove_filters.configure(state="normal")
            if self.num_items:
                self.progress_bar_label.configure(text=self.status_message)
                self.num_items = None
            else:
                self.progress_bar_label.configure(text="filter applied")

            self.workflow_versions = df["Version"].unique()

            self.table_created = True
            self.table_present = True

    def getStatuses(self):
        start_time = time.time()
        workers = int(self.search_entry.get())
        print(f"Number of Workers: {workers}")

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

        
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(fetch_status, self.guids_array))
        
        end_time = time.time()  # Record the end time
        self.elapsed_time = end_time - start_time  # Calculate the elapsed time

        self.status_message=f"statuses retrieved in {self.elapsed_time:.2f} seconds"

        self.num_items = len(self.guids_array)
        self.workflow_statuses = pd.DataFrame(results)
        self.filtered_df = pd.DataFrame()
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

    def export_to_csv(self, filename, df=pd.DataFrame()):
        
        try:
            self.warn_window.destroy()
        except:
            print("No Warn Window")

        if not df.empty:
            current_df = df       
        elif not self.filtered_df.empty:
            current_df = self.filtered_df
        else:
            current_df = self.workflow_statuses
        
        current_df.to_csv("../../"+filename, index=False)

        self.output_window = OutputWindow(self)
        self.output_window.grab_set()
        self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"CSV file saved as {filename}")
        self.output_window.output_label.grid(row=0, column=0, pady=15)

    def start_upgrade(self):

        self.upgrade_button.configure(state="disabled")
        self.search_guids_button.configure(state="disabled")
        
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
            workers = int(self.search_entry.get())
            if self.filtered_df.empty:
                current_df = self.workflow_statuses
            else:
                current_df = self.filtered_df
            self.progress_bar_label.configure(text=f"Upgrading {len(list(current_df['Product ID']))} items with {workers} workers.")
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

    def upgrade_items(self, wk_num=0, df=pd.DataFrame):
        start_time = time.time()  # Record the start time
        
        if wk_num > 0:
            workers = wk_num
        else:
            workers = int(self.search_entry.get())
        print(f"Number of Workers: {workers}")

        if not df.empty:
            current_df = df
        elif self.filtered_df.empty:
            current_df = self.workflow_statuses
            # print("Using Original DF")
        else:
            current_df = self.filtered_df
            # print("Using filtered DF")

        product_ids = list(current_df["Product ID"])
        self.num_items = len(product_ids)
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as exec:
            exec.map(process_upgrade, product_ids)

        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time

        self.upgrade_data = {
            "Product GUIDs": product_ids,
            "Success": success
        }
        self.status_message= f"Upgrade completed in {elapsed_time:.2f} seconds"

        if df.empty:
            self.after(0, self.upgrade_output)
        else:
            self.product_search_window.stop_event.set()
            self.after(0, self.product_search_window.stop_progress_bar)

    def upgrade_output(self):
        self.progress_bar.set(1)
        self.progress_bar.stop()

        self.search_guids_button.configure(state="normal")
        self.upgrade_button.configure(state="normal")

        self.progress_bar_label.configure(text=self.status_message)

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
        self.product_window.geometry("350x550+500+200")
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
            self.product_window.products_frame.i.select()
            checkboxes.append(self.product_window.products_frame.i)
            ind += 1
            
        self.product_window.ok_button = customtkinter.CTkButton(self.product_window, text ="Filter", command=lambda: [self.filter_products(checkboxes),self.product_window.destroy()])
        self.product_window.ok_button.grid(row=2, column=0, pady=15)

        self.product_window.select_all = customtkinter.CTkCheckBox(self.product_window, text="Select All", command=lambda: self.select_all(checkboxes))
        self.product_window.select_all.grid(row=0,column=0,pady=(20,5))
        self.product_window.select_all.select()

    def select_all(self, value_list):
        
        choice = self.product_window.select_all.get()
        
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
        # self.table.destroy()
        self.create_table(self.filtered_df)

        return None

    def status_select(self):
        self.product_window = customtkinter.CTkToplevel(self)
        self.product_window.geometry("350x550+500+200")
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

        self.product_window.ok_button = customtkinter.CTkButton(self.product_window, text ="Filter", command=lambda: [self.filter_status(checkboxes),self.product_window.destroy()])
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
        # self.table.destroy()
        self.create_table(self.filtered_df)

        return None

    def version_select(self):
        self.product_window = customtkinter.CTkToplevel(self)
        self.product_window.geometry("180x300+500+200")
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

        self.product_window.ok_button = customtkinter.CTkButton(self.product_window, text ="Filter", command=lambda: [self.filter_version(checkboxes),self.product_window.destroy()])
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

        
        if self.filtered_df.empty:
            current_df = self.workflow_statuses
            # print("Using Original DF")
        else:
            current_df = self.filtered_df
            # print("Using filtered_df")

        self.filtered_df = current_df[current_df["Version"].isin(to_filter)]
        self.filtered_df.reset_index(drop=True,inplace=True)
        
        self.workflow_versions = to_filter

        self.table_created = False
        # self.table.destroy()
        self.create_table(self.filtered_df)

        return None

    def remove_filters(self):
        self.filtered_df = self.workflow_statuses
        self.table_created = False
        # self.table.destroy()
        self.create_table(self.workflow_statuses)

    def save_workflow(self):

        list_values= []

        if not self.saved_workflows:
            list_values = [self.workflow_values]
            with open("saved_workflows.json", 'w') as json_file:
                json.dump(list_values, json_file)
            self.load_saved_workflows()
        else:
            list_values = self.saved_workflows
            list_values.append(self.workflow_values)
            with open("saved_workflows.json", 'w') as json_file:
                json.dump(list_values, json_file)
            self.load_saved_workflows()
        
        ok_pressed = CTkMessagebox(title="Workflow_ext", message="Workflow Saved!", icon="check", option_1="Ok")
        response = ok_pressed.get()
        if response== "Ok":
            ok_pressed.destroy()

    def load_saved_workflows(self):
        try:
            with open("saved_workflows.json", 'r') as json_file:
                self.saved_workflows = json.load(json_file)
        except FileNotFoundError:
        # Handle the case where the file doesn't exist
            print("The 'saved_workflows.json' file does not exist.")
            self.saved_workflows = []  # You can initialize it as an empty list or handle it differently based on your needs
        except Exception as e:
            # Handle other potential exceptions
            print(f"An error occurred: {str(e)}")
            self.saved_workflows = []

        if self.saved_workflows:
            wf_labels = []
            for i in self.saved_workflows:
                wf_labels.append(i[0])
            self.workflow_selector.configure(values=wf_labels)
            self.workflow_selector.set("--saved workflows--")

    def load_workflow(self,x):
        print(x)
        if self.workflow_selector.get() == "--saved workflows--":
            return None
        else:
            for i in self.saved_workflows:
                if i[0]==self.workflow_selector.get():
                    self.workflow_id.delete(0,last_index=50)
                    self.workflow_id.insert(0,i[1])
                    self.workflow_dataowner.delete(0,last_index=50)
                    self.workflow_dataowner.insert(0,i[2])
                    self.environment_selector.set(i[3])
                    break

    def start_restart(self):

        self.restart_button.configure(state="disabled")
        self.search_guids_button.configure(state="disabled")
        
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
            workers = int(self.search_entry.get())
            if self.filtered_df.empty:
                current_df = self.workflow_statuses
            else:
                current_df = self.filtered_df
            self.progress_bar_label.configure(text=f"Restarting {len(list(current_df['Product ID']))} items with {workers} workers.")
            self.progress_bar.set(0)
            self.progress_bar.start()

            restart_thread = threading.Thread(target=self.restart_items)
            restart_thread.start()    

    def restart_items(self, wk_num=0, df=pd.DataFrame):
        start_time = time.time()  # Record the start time
        if wk_num > 0:
            workers = wk_num
        else:
            workers = int(self.search_entry.get())
        print(f"Number of Workers: {workers}")

        if not df.empty:
            current_df = df
        elif self.filtered_df.empty:
            current_df = self.workflow_statuses
            # print("Using Original DF")
        else:
            current_df = self.filtered_df
            # print("Using filtered DF")

        product_ids = list(current_df["Product ID"])
        self.num_items = len(product_ids)
        instance_ids = current_df["Instance ID"]

        upgrade_url = f"https://{self.env_url}/api/workflow/Debug/restart/{self.workflowId}/"

        success = []
        self.true_num = 0
        self.false_num = 0

        def process_restart(guid):
            instance_index = product_ids.index(guid)  # Get the index for the current GUID
            url = f"{upgrade_url}{instance_ids[instance_index]}/{guid}"
           
            response = requests.get(url, headers=self.headers)
            
            if response.status_code == 200:
                success.append(True)
                new_instance_id = response.json()  # Replace with the actual response attribute
                current_df.at[instance_index, "Instance ID"] = new_instance_id
                self.true_num += 1
            else:
                success.append(False)
                self.false_num += 1

        # Use a ThreadPoolExecutor with a maximum of 20 workers
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as exec:
            exec.map(process_restart, product_ids)

        end_time = time.time()  # Record the end time
        elapsed_time = end_time - start_time  # Calculate the elapsed time

        self.restart_data = {
            "Product GUIDs": product_ids,
            "Success": success
        }
        print(f"Upgrade completed in {elapsed_time:.2f} seconds. {self.true_num} items")
        self.status_message= f"Restart completed in {elapsed_time:.2f} seconds"
        self.filtered_df = current_df
        
        if df.empty:
            self.after(0, self.restart_output)
        else:
            self.product_search_window.stop_event.set()
            self.after(0, self.product_search_window.stop_progress_bar)  
    
    def restart_output(self):
        self.progress_bar.set(1)
        self.progress_bar.stop()
        self.restart_button.configure(state="normal")
        self.restart_window = customtkinter.CTkToplevel(self)
        self.restart_window.geometry("400x150+500+500")

        #update table
        self.progress_bar_label.configure(text=self.status_message)
        self.search_guids_button.configure(state="normal")
        print("re-creating table")
        self.table_created = False
        self.create_table(self.filtered_df)

        #open results window
        self.restart_window.grid_columnconfigure((0,1), weight=1)
        self.restart_window.grid_rowconfigure((0,1), weight=1)
        self.restart_window.grab_set()
        self.restart_window.output_label = customtkinter.CTkLabel(self.restart_window, text=f"{self.true_num} items restarted")
        self.restart_window.output_label.grid(row=0, column=0, padx=5, pady=5)
        self.restart_window.output_label2 = customtkinter.CTkLabel(self.restart_window, text=f"{self.false_num} items failed to restart")
        self.restart_window.output_label2.grid(row=1, column=0, padx=5, pady=5)
        self.restart_window.ok_button = customtkinter.CTkButton(self.restart_window, text="Ok", command = self.restart_window.destroy)
        self.restart_window.ok_button.grid(row=0, column=1, padx=5, pady=5)
        self.restart_window.export_button = customtkinter.CTkButton(self.restart_window, text="Export", command =lambda: self.export_restarts(self.restart_data,self.restart_window))
        self.restart_window.export_button.grid(row=1, column=1, padx=5, pady=5)

    def export_restarts(self, data, restart_window):
        restart_window.destroy()

        df = pd.DataFrame(data)
        df.to_csv("../../restart_results.csv", index=False)

        self.output_window = OutputWindow(self)
        self.output_window.grab_set()
        self.output_window.output_label = customtkinter.CTkLabel(self.output_window, text=f"Results saved to restart_results.csv")
        self.output_window.output_label.grid(row=0, column=0, pady=15)

    def open_product_search(self):
        
        self.product_search_window = ProductSearchWindow()
        self.product_search_window.grab_set()


if __name__ == "__main__":
    app = WorkflowEnhance()
    app.mainloop()