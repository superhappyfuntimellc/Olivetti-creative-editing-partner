const STORAGE_KEY = "todo-app-v1";

const input = document.getElementById("new-todo");
const list = document.getElementById("todo-list");
const count = document.getElementById("count");
const clearBtn = document.getElementById("clear-completed");

let todos = JSON.parse(localStorage.getItem(STORAGE_KEY)) || [];

function save() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(todos));
}

function render(filter = "all") {
  list.innerHTML = "";

  let filtered = todos;
  if (filter === "active") filtered = todos.filter(t => !t.done);
  if (filter === "completed") filtered = todos.filter(t => t.done);

  filtered.forEach((todo, i) => {
    const li = document.createElement("li");

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = todo.done;
    checkbox.onchange = () => {
      todo.done = checkbox.checked;
      save();
      render(filter);
    };

    const span = document.createElement("span");
    span.textContent = todo.text;
    if (todo.done) span.classList.add("completed");

    li.append(checkbox, span);
    list.appendChild(li);
  });

  const activeCount = todos.filter(t => !t.done).length;
  count.textContent = `${activeCount} items left`;
}

input.addEventListener("keydown", e => {
  if (e.key === "Enter" && input.value.trim()) {
    todos.push({ text: input.value.trim(), done: false });
    input.value = "";
    save();
    render();
  }
});

clearBtn.onclick = () => {
  todos = todos.filter(t => !t.done);
  save();
  render();
};

render();
