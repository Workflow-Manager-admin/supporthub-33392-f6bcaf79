import React, { useState, useEffect } from 'react';
import './App.css';

// PUBLIC_INTERFACE
function App() {
  // Authentication state and pseudo-user handling
  const [user, setUser] = useState(null);
  // Ticket states
  const [tickets, setTickets] = useState([]);
  const [filters, setFilters] = useState({ status: "all" });
  const [showTicketModal, setShowTicketModal] = useState(false);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [showCreateForm, setShowCreateForm] = useState(false);

  // Sample ticket data for initial UI prototype
  useEffect(() => {
    setTickets([
      {
        id: 1,
        title: "Can't login to my account",
        description: "I tried resetting password but still can't get in.",
        status: "open",
        created_by: "alice",
        created_at: "2024-04-11 10:00",
      },
      {
        id: 2,
        title: "App crashes on ticket update",
        description: "When I update a ticket status, the app crashes to desktop.",
        status: "in_progress",
        created_by: "bob",
        created_at: "2024-04-10 16:24",
      }
    ]);
  }, []);

  // PUBLIC_INTERFACE
  function handleLogin(username, password) {
    // Dummy login for UI (replace with API later)
    if (username && password) setUser({ username });
  }

  // PUBLIC_INTERFACE
  function handleLogout() {
    setUser(null);
  }

  // PUBLIC_INTERFACE
  function handleCreateTicket(newTicket) {
    setTickets([
      {
        ...newTicket,
        id: Date.now(),
        status: "open",
        created_by: user.username,
        created_at: new Date().toLocaleString(),
      },
      ...tickets,
    ]);
    setShowCreateForm(false);
  }

  // PUBLIC_INTERFACE
  function handleStatusUpdate(ticketId, newStatus) {
    setTickets(tickets =>
      tickets.map(t =>
        t.id === ticketId ? { ...t, status: newStatus } : t
      )
    );
    setSelectedTicket(null);
    setShowTicketModal(false);
  }

  // PUBLIC_INTERFACE
  function filteredTickets() {
    if (filters.status === "all") return tickets;
    return tickets.filter(ticket => ticket.status === filters.status);
  }

  // PUBLIC_INTERFACE
  function openTicketModal(ticket) {
    setSelectedTicket(ticket);
    setShowTicketModal(true);
  }

  // PUBLIC_INTERFACE
  function closeTicketModal() {
    setShowTicketModal(false);
    setSelectedTicket(null);
  }

  // Layout sections
  if (!user) {
    return (
      <div className="app light-theme">
        <Header user={null} onLogout={handleLogout} />
        <div className="login-wrapper">
          <LoginForm onLogin={handleLogin} />
        </div>
      </div>
    );
  }

  return (
    <div className="app light-theme">
      <Header user={user} onLogout={handleLogout} />
      <div className="main-area">
        <Sidebar
          filters={filters}
          setFilters={setFilters}
          onCreateTicket={() => setShowCreateForm(true)}
        />
        <main className="ticket-list-area">
          <div className="ticket-list-header">
            <h2>Support Tickets</h2>
            <button className="btn btn-accent" onClick={() => setShowCreateForm(true)}>
              + New Ticket
            </button>
          </div>
          <TicketList tickets={filteredTickets()} onTicketClick={openTicketModal} />
        </main>
      </div>
      {showCreateForm && (
        <TicketCreateForm
          user={user}
          onCreate={handleCreateTicket}
          onClose={() => setShowCreateForm(false)}
        />
      )}
      {showTicketModal && selectedTicket && (
        <TicketDetailModal
          ticket={selectedTicket}
          onClose={closeTicketModal}
          onStatusUpdate={handleStatusUpdate}
        />
      )}
    </div>
  );
}

// PUBLIC_INTERFACE
function Header({ user, onLogout }) {
  return (
    <nav className="navbar">
      <div className="header-logo">
        <span className="logo-symbol" style={{ color: "var(--primary)" }}>*</span>
        SupportHub
      </div>
      <div className="header-right">
        {user && (
          <>
            <span style={{ marginRight: '1rem', color: "var(--text-secondary)" }}>
              {user.username}
            </span>
            <button className="btn btn-secondary" onClick={onLogout}>
              Log Out
            </button>
          </>
        )}
      </div>
    </nav>
  );
}

// PUBLIC_INTERFACE
function LoginForm({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  return (
    <form className="login-form" onSubmit={e => { e.preventDefault(); onLogin(username, password); }}>
      <h2>Login to SupportHub</h2>
      <input
        className="input"
        placeholder="Username"
        value={username}
        onChange={e => setUsername(e.target.value)}
        autoFocus
        required
        />
      <input
        className="input"
        type="password"
        placeholder="Password"
        value={password}
        required
        onChange={e => setPassword(e.target.value)}
      />
      <button className="btn btn-primary btn-large" type="submit">
        Login
      </button>
    </form>
  );
}

// PUBLIC_INTERFACE
function Sidebar({ filters, setFilters, onCreateTicket }) {
  return (
    <aside className="sidebar">
      <h3>Filters</h3>
      <div className="filter-group">
        <label>Status:</label>
        <select
          className="input"
          value={filters.status}
          onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}
        >
          <option value="all">All</option>
          <option value="open">Open</option>
          <option value="in_progress">In Progress</option>
          <option value="resolved">Resolved</option>
          <option value="closed">Closed</option>
        </select>
      </div>
      <button className="btn btn-accent" onClick={onCreateTicket} style={{ marginTop: 18 }}>
        + New Ticket
      </button>
    </aside>
  );
}

// PUBLIC_INTERFACE
function TicketList({ tickets, onTicketClick }) {
  if (!tickets.length) {
    return <div className="ticket-list-empty">No tickets found.</div>;
  }
  return (
    <div className="ticket-list-table">
      <div className="ticket-list-row ticket-list-header-row">
        <div>ID</div>
        <div>Title</div>
        <div>Status</div>
        <div>Created By</div>
        <div>Created At</div>
      </div>
      {tickets.map(ticket => (
        <div
          key={ticket.id}
          className="ticket-list-row ticket-list-item"
          onClick={() => onTicketClick(ticket)}
        >
          <div>{ticket.id}</div>
          <div>{ticket.title}</div>
          <div>
            <span className={"badge " + ticket.status}>{ticket.status.replace("_", " ")}</span>
          </div>
          <div>{ticket.created_by}</div>
          <div>{ticket.created_at}</div>
        </div>
      ))}
    </div>
  );
}

// PUBLIC_INTERFACE
function TicketDetailModal({ ticket, onClose, onStatusUpdate }) {
  const statusOptions = [
    { key: "open", label: "Open" },
    { key: "in_progress", label: "In Progress" },
    { key: "resolved", label: "Resolved" },
    { key: "closed", label: "Closed" },
  ];
  return (
    <div className="modal-overlay">
      <div className="modal-content ticket-detail-modal">
        <button className="modal-close" onClick={onClose}>&times;</button>
        <h2>Ticket #{ticket.id}</h2>
        <div className="ticket-detail-field">
          <strong>Title:</strong> {ticket.title}
        </div>
        <div className="ticket-detail-field">
          <strong>Description:</strong>
          <div className='ticket-detail-description'>{ticket.description}</div>
        </div>
        <div className="ticket-detail-field">
          <strong>Status:</strong>
          <span className={"badge " + ticket.status}>{ticket.status.replace("_", " ")}</span>
          <span style={{ marginLeft: 8 }}>
            <select
              className="input"
              style={{ marginLeft: 8 }}
              value={ticket.status}
              onChange={e => onStatusUpdate(ticket.id, e.target.value)}
            >
              {statusOptions.map(opt => (
                <option value={opt.key} key={opt.key}>{opt.label}</option>
              ))}
            </select>
          </span>
        </div>
        <div className="ticket-detail-field">
          <strong>Created By:</strong> {ticket.created_by}
        </div>
        <div className="ticket-detail-field">
          <strong>Created At:</strong> {ticket.created_at}
        </div>
      </div>
    </div>
  );
}

// PUBLIC_INTERFACE
function TicketCreateForm({ onClose, onCreate }) {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  return (
    <div className="modal-overlay">
      <div className="modal-content ticket-create-form">
        <button className="modal-close" onClick={onClose}>&times;</button>
        <h2>Create New Ticket</h2>
        <form onSubmit={e => {
          e.preventDefault();
          if (title.trim() && description.trim())
            onCreate({ title, description });
        }}>
          <input
            className="input"
            placeholder="Ticket title"
            value={title}
            required
            onChange={e => setTitle(e.target.value)}
          />
          <textarea
            className="input"
            placeholder="Describe your issue"
            value={description}
            rows={5}
            required
            onChange={e => setDescription(e.target.value)}
          />
          <div className="modal-actions">
            <button className="btn btn-primary btn-large" type="submit">
              Create
            </button>
            <button className="btn btn-secondary btn-large" style={{ marginLeft: 8 }} type="button" onClick={onClose}>
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default App;
