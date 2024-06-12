import random
import os
import sys
import time
import tkinter as tk
from tkinter import ttk, simpledialog
import tkinter.font as tkFont

def get_top_four_pick_pct(initialProbs, num_of_teams):
    secondProbs = [0.] * num_of_teams
    thirdProbs = [0.] * num_of_teams
    fourthProbs = [0.] * num_of_teams
    top_four_probs = [0.] * num_of_teams

    for i in range(num_of_teams):
        #Team i selected first, eliminate their probability
        firstRemoved = initialProbs[:i] + [0.] + initialProbs[i+1:]
        #Renormalize probabilities for remaining teams to get second pick distribution
        totalProb = sum(firstRemoved)
        conditionalProbs = [initialProbs[i] * x / totalProb for x in firstRemoved]
        #Append conditional probability given Team i
        secondProbs = [x + y for x,y in zip(secondProbs, conditionalProbs)]

        for j in range(num_of_teams):
            if i != j:
                secondRemoved = firstRemoved[:j] + [0.] + firstRemoved[j+1:]
                totalProb = sum(secondRemoved)
                conditionalProbs2 = [conditionalProbs[j] * x / totalProb for x in secondRemoved]
                thirdProbs = [x + y for x, y in zip(thirdProbs, conditionalProbs2)]
            
                for k in range(num_of_teams):
                    if i != k:
                        if j != k:
                            thirdRemoved = secondRemoved[:k] + [0.] + secondRemoved[k+1:]
                            totalProb = sum(thirdRemoved)
                            conditionalProbs3 = [conditionalProbs2[k] * x / totalProb for x in thirdRemoved]
                            fourthProbs = [x + y for x, y in zip(fourthProbs, conditionalProbs3)]
        
    # print(secondProbs)
    # print(thirdProbs)
    # print(fourthProbs)

    for i in range(num_of_teams):
        top_four_probs[i] = initialProbs[i] + secondProbs[i] + thirdProbs[i] + fourthProbs[i]
    # print(top_four_probs)

    return top_four_probs

class EditableTreeview(ttk.Treeview):
    """A Treeview widget with in-place editing for probabilities."""
    def __init__(self, parent, **kw):
        super().__init__(parent, **kw)
        self._cur_item = None
        self._cur_col = None
        self.bind("<Double-1>", self._on_double_click)
        self.entry = None
        self.editable = True

    def _on_double_click(self, event):
        if not self.editable:
            return
        if self.entry:
            self.entry.destroy()  # Remove any existing entry widget

        row_id = self.identify_row(event.y)
        column = self.identify_column(event.x)
        self._cur_item = row_id
        self._cur_col = column

        if not row_id or column != "#2":  # Make only the 'Probability' column editable
            return

        x, y, width, height = self.bbox(row_id, column)
        self.entry = ttk.Entry(self, width=width)
        self.entry.place(x=x, y=y, width=width, height=height)
        self.entry.focus()

        col_index = int(column.replace('#', '')) - 1
        current_value = self.item(row_id, 'values')[col_index]
        self.entry.insert(0, current_value)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Return>", self._save_edited_value)

    def _on_focus_out(self, event):
        self._save_edited_value(event)
        if self.entry: # Ensure self.entry is not None before destroying it
            self.entry.destroy()
            self.entry = None

    def _save_edited_value(self, event):
        new_value = self.entry.get()
        if not new_value.endswith('%'):
            new_value = f"{new_value}%"
        values = list(self.item(self._cur_item, 'values'))
        col_index = int(self._cur_col.replace('#', '')) - 1
        values[col_index] = new_value
        self.item(self._cur_item, values=values)
        self.entry.destroy()
        self.entry = None

class DraftPickerApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Draft Picker")

        # Determine the base path for resources
        if hasattr(sys, '_MEIPASS'):
            self.base_path = sys._MEIPASS
        else:
            self.base_path = os.path.abspath(".")

        # Load and set the window icon
        icon_path = os.path.join(self.base_path, "basketball.png")
        self.master.iconphoto(True, tk.PhotoImage(file=icon_path))

        # Load the logo image
        logo_path = os.path.join(self.base_path, "basketball.png")
        self.logo_image = tk.PhotoImage(file=logo_path)
        
        # Define Korean font
        self.korean_font = tkFont.Font(family="맑은 고딕", size=10)

        # # Define colors for teams
        self.team_colors = {
            'team1': '#FF6347',   
            'team2': '#00FFFF',  
            'team3': '#FF4500',  
            'team4': '#00BFFF',   
            'team5': '#FFD700',  
            'team6': '#8A2BE2',  
            'team7': '#7FFF00', 
            'team8': '#FF69B4',  
            'team9': '#32CD32',  
            'team10': '#DC143C', 
            'team11': '#ADFF2F', 
            'team12': '#DAA520' 
        }

        # Create frames for layout
        self.top_left_frame = tk.Frame(master, bg="lightgrey")
        self.top_left_frame.grid(row=0, column=0, sticky="nsew")

        self.right_frame = tk.Frame(master, bg="lightgrey", width=200)
        self.right_frame.grid(row=0, column=1, sticky="ns")

        self.bottom_frame = tk.Frame(master, bg="lightgrey", height=200)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Configure grid to adjust layout
        self.master.grid_rowconfigure(0, weight=1)
        self.master.grid_columnconfigure(0, weight=1)
        self.master.grid_columnconfigure(1, weight=0)
        self.master.grid_rowconfigure(1, weight=0)

        # Canvas for shuffling animation
        self.canvas = tk.Canvas(self.top_left_frame, bg="black")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.tree = EditableTreeview(self.bottom_frame, columns=('Team', 'Probability', 'Top 4 Chance'), show='headings', height=12)
        self.tree.heading('Team', text='팀명')
        self.tree.heading('Probability', text='다음 픽 확률', anchor='center')
        self.tree.heading('Top 4 Chance', text='다음 4픽 확률', anchor='center')
        self.tree.column('Team', width=60, anchor='w')
        self.tree.column('Probability', width=100, anchor='center')
        self.tree.column('Top 4 Chance', width=120, anchor='center')
        self.tree.pack(fill=tk.X)

        # Text widget for displaying picked teams
        self.picked_teams_text = tk.Text(self.right_frame, width=30, state=tk.DISABLED)
        self.picked_teams_text.pack(fill=tk.Y, expand=True)
        self.picked_teams_text.configure(font=self.korean_font)

        self.teams = ['team1', 'team2', 'team3', 'team4', 'team5', 'team6', 'team7', 'team8', 'team9', 'team10', 'team11', 'team12']
        self.weights = [14.1, 14.1, 14.1, 12.6, 10.9, 9.1, 7.6, 6.1, 4.6, 3.1, 2.1, 1.6]  # Hardcoded weights
        self.probabilities = self.normalize_weights(self.weights)
        self.top4_chances = self.calculate_top4_chances(self.probabilities)

        self.update_tree()
        self.initialize_picked_teams_list()

        self.update_button = tk.Button(self.bottom_frame, text="확률 조정 후 클릭 (각 팀 확률 더블클릭 시 조정 가능)", command=self.update_probabilities)
        self.update_button.pack(side=tk.TOP, pady=10)

        self.draft_button = tk.Button(self.right_frame, text="Draft 시작", command=self.toggle_draft)
        self.draft_button.pack(side=tk.TOP, pady=10)

        self.draft = None
        self.is_shuffling = False

    def normalize_weights(self, weights):
        total_weight = sum(weights)
        if total_weight > 0:
            return [f"{(w / total_weight) * 100:.2f}%" for w in weights]
        else:
            return [f"{100 / len(weights):.2f}%" for _ in weights]

    def calculate_top4_chances(self, probabilities):
        num_teams = len(probabilities)
        if num_teams <= 4:
            return [f"{100:.2f}%" for _ in range(num_teams)]

        weights = [float(p.strip('%')) / 100 for p in probabilities]
        top4_chances = get_top_four_pick_pct(weights, num_teams)
        return [f"{chance * 100:.2f}%" for chance in top4_chances]

    def update_tree(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for idx, (team, prob, top4) in enumerate(zip(self.teams, self.probabilities, self.top4_chances)):
            bg_color = '#f0f0f0' if idx % 2 == 0 else '#ffffff'
            self.tree.insert('', 'end', values=(team, prob, top4), tags=('oddrow' if idx % 2 == 0 else 'evenrow'))
        self.tree.tag_configure('oddrow', background='#f0f0f0')
        self.tree.tag_configure('evenrow', background='#ffffff')

    def update_probabilities(self):
        self.teams, self.weights = [], []
        for child in self.tree.get_children():
            team, weight, _ = self.tree.item(child, 'values')
            self.teams.append(team)
            try:
                weight = float(weight.strip('%'))
            except ValueError:
                weight = 0
            self.weights.append(weight)

        # Normalize weights so they sum to 100%
        self.probabilities = self.normalize_weights(self.weights)
        self.top4_chances = self.calculate_top4_chances(self.probabilities)

        # Sort the teams by probability
        teams_with_probs = sorted(zip(self.teams, self.probabilities, self.top4_chances), key=lambda x: float(x[1].strip('%')), reverse=True)
        self.teams, self.probabilities, self.top4_chances = map(list, zip(*teams_with_probs))

        self.update_tree()
        self.display_status_message("확률 조정 완료")

    def toggle_draft(self):
        if not self.draft or not self.draft.teams:
            self.tree.editable = False #Disable editing
            self.update_button.config(state=tk.DISABLED) #disable "update probabilites" button
            self.draft = DraftPicker(self.teams, self.probabilities)
            self.countdown(5)
            self.draft_button.config(text="다음 픽")
        else:
            self.next_pick()

    def toggle_fullscreen(self, fullscreen):
        self.master.attributes("-fullscreen", fullscreen)
        self.master.update()

    # shuffle without grid
    # def shuffle_teams(self):
    #     shuffle_duration = 3  # seconds
    #     shuffle_speed = 0.05  # seconds per shuffle step
    #     end_time = time.time() + shuffle_duration

    #     weighted_team_list = self.generate_weighted_team_list()
    #     canvas_window_size = self.canvas.winfo_width() * self.canvas.winfo_height()

    #     while time.time() < end_time:
    #         self.canvas.delete("all")
    #         random.shuffle(weighted_team_list)
            
    #         for team in weighted_team_list[:(canvas_window_size // 700)]:  # Display a subset for visibility
    #             color = self.team_colors.get(team, "#000000")  # Default to black if no color found
    #             x = random.randint(0, self.canvas.winfo_width())
    #             y = random.randint(0, self.canvas.winfo_height())
    #             self.canvas.create_text(x, y, text=team, fill=color, font=("맑은 고딕", 14))
            
    #         self.master.update()
    #         time.sleep(shuffle_speed)

    def shuffle_teams(self):
        shuffle_duration = 3  # seconds
        shuffle_speed = 0.05  # seconds per shuffle step
        end_time = time.time() + shuffle_duration

        weighted_team_list = self.generate_weighted_team_list()

        text_width = 40  # Approximate width of each text item
        text_height = 25  # Approximate height of each text item

        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # Calculate number of rows and columns based on text size and canvas size
        num_columns = canvas_width // text_width
        num_rows = canvas_height // text_height

        # Generate grid positions
        grid_positions = [(col * text_width, row * text_height) for row in range(num_rows) for col in range(num_columns)]

        while time.time() < end_time:
            self.canvas.delete("all")
            random.shuffle(weighted_team_list)
            random.shuffle(grid_positions)
            
            # Display team names in grid positions with background colors
            for team, (x, y) in zip(weighted_team_list[:min(len(grid_positions), len(weighted_team_list))], grid_positions):
                bg_color = self.team_colors.get(team, "#000000")  # Default to black if no color found
                text_color = "#FFFFFF"  # Default text color

                # Draw rectangle with background color
                self.canvas.create_rectangle(x, y, x + text_width, y + text_height, fill=bg_color, outline=bg_color)

                # Draw text on top of the rectangle
                self.canvas.create_text(x + text_width // 2, y + text_height // 2, text=team, fill=text_color, font=("맑은 고딕", 14))
        
            self.master.update()
            time.sleep(shuffle_speed)


    def next_pick(self):
        if self.is_shuffling:
            return # prevent next pick during shuffling

        self.is_shuffling = True # Set the flag to indicate shuffling is in progress
        self.draft_button.config(state=tk.DISABLED) # disable next pick button

        self.shuffle_teams() # Add shuffling before picking teams

        self.is_shuffling = False # Reset the flag after shuffling is done
        self.draft_button.config(state=tk.NORMAL) #Re-enable next pick button

        current_pick, probabilities, top_picks = self.draft.next_pick()
        self.teams = [team for team, prob in probabilities]
        self.probabilities = [f"{prob * 100:.2f}%" for team, prob in probabilities]
        self.top4_chances = self.calculate_top4_chances(self.probabilities)

        self.update_tree()

        if current_pick:
            self.update_picked_teams_list(current_pick)
            self.display_picked_team(current_pick)

            if not probabilities:
                self.canvas.insert(tk.END, "Draft 완료!\n")
                self.draft_button.config(state=tk.DISABLED, text="Draft 완료")
        else:
            self.canvas.insert(tk.END, "Draft 완료!\n")
            self.draft_button.config(state=tk.DISABLED, text="Draft 완료")

    def initialize_picked_teams_list(self):
        self.picked_teams_text.config(state=tk.NORMAL)
        self.picked_teams_text.delete(1.0, tk.END)

        # Configure tags for alternating colors
        self.picked_teams_text.tag_configure('evenrow', background='#f0f0f0', font=('맑은 고딕', 14))
        self.picked_teams_text.tag_configure('oddrow', background='#ffffff', font=('맑은 고딕', 14))

        for i in range(1, len(self.teams) + 1):
            tag = 'oddrow' if i % 2 != 0 else 'evenrow'
            if i < 10:
                self.picked_teams_text.insert(tk.END, f"  {i}. \n", (tag,))
            else:
                self.picked_teams_text.insert(tk.END, f" {i}. \n", (tag,))
        self.picked_teams_text.config(state=tk.DISABLED)

    def update_picked_teams_list(self, team):
        self.picked_teams_text.config(state=tk.NORMAL)
        current_content = self.picked_teams_text.get(1.0, tk.END).splitlines()

        for i, line in enumerate(current_content):
            if line.endswith(". "):
                if i < 9:
                    current_content[i] = f"  {i + 1}. {team}"
                    break
                else:
                    current_content[i] = f" {i + 1}. {team}"
                    break

        self.picked_teams_text.delete(1.0, tk.END)
        for idx, line in enumerate(current_content):
            if line.strip():
                tag = 'oddrow' if idx % 2 == 0 else 'evenrow'
                self.picked_teams_text.insert(tk.END, line + "\n", (tag,))
        self.picked_teams_text.config(state=tk.DISABLED)

    def generate_weighted_team_list(self):
        weighted_team_list = []
        for team, prob in zip(self.teams, self.probabilities):
            weight = int(float(prob.strip('%')) * 100)
            weighted_team_list.extend([team] * weight)

        return weighted_team_list

    def display_status_message(self, message):
        self.canvas.delete("all")  # Clear the canvas
        center_x = self.canvas.winfo_width() / 2
        center_y = self.canvas.winfo_height() / 2
        large_font = tkFont.Font(family="맑은 고딕", size=24, weight="bold")
        item = self.canvas.create_text(center_x, center_y, text=message, fill="#FAFAFA", font=large_font, tags="status_message")
        self.master.update()
        self.master.after(1000, self.fade_away, item)

    def countdown(self, count):
        if count > 0:
            self.display_status_message(f"{count}")
            self.master.after(1000, self.countdown, count-1)
        else:
            self.display_status_message("Draft 시작!")
            self.master.after(1000, self.next_pick)

    def start_shuffle(self):
        self.next_pick()

    def fade_away(self, item, steps=100):
        def fade(step):
            if step < steps:
                alpha = int(255 * (1 - step / steps))
                color = f"#{alpha:02x}{alpha:02x}{alpha:02x}"
                self.canvas.itemconfig(item, fill=color)
                self.master.after(10, fade, step + 1)
            else:
                self.canvas.delete(item)
        fade(0)

    def display_picked_team(self, team):
        center_x = self.canvas.winfo_width() / 2
        center_y = self.canvas.winfo_height() / 2
        large_font = tkFont.Font(family="맑은 고딕", size=60, weight="bold")
        color = self.team_colors.get(team, "#000000")

        # Draw outline or shadow
        offsets = [(-3, -3), (3, -3), (-3, 3), (3, 3)]
        for dx, dy in offsets:
            self.canvas.create_text(center_x + dx, center_y + dy, text=team, fill="black", font=large_font, tags="picked_team_outline")#ECECEC
    
        self.canvas.create_text(center_x, center_y, text=team, fill=color, font=large_font, tags="picked_team")


class DraftPicker:
    def __init__(self, teams, probabilities):
        self.teams = list(teams)  # Convert tuple to list if necessary
        self.probabilities = [float(p.strip('%')) / 100 for p in probabilities]
        self.draft_order = []

    def next_pick(self):
        if not self.teams:
            return None, [], []

        chosen_team = random.choices(self.teams, self.probabilities, k=1)[0]
        chosen_index = self.teams.index(chosen_team)
        self.draft_order.append(chosen_team)

        del self.teams[chosen_index]
        del self.probabilities[chosen_index]

        total_prob = sum(self.probabilities)
        if total_prob > 0:
            probabilities = [(team, prob / total_prob) for team, prob in zip(self.teams, self.probabilities)]
            top_picks = sorted(probabilities, key=lambda x: x[1], reverse=True)[:4]
        else:
            probabilities = [(team, 0) for team in self.teams]
            top_picks = probabilities[:4]

        return chosen_team, probabilities, top_picks

if __name__ == "__main__":
    root = tk.Tk()
    app = DraftPickerApp(root)
    root.mainloop()
