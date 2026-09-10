import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  Search,
  RefreshCw,
  UserPlus,
  Users,
  MessageCircle,
  X,
  User,
  Phone,
  Smartphone,
} from "lucide-react";

import {
  createCustomer,
  getCustomers,
} from "../../api/customers";

import type { Customer } from "../../types/customer";
import useDashboardWebSocket, {
  type DashboardEvent,
} from "../../hooks/useDashboardWebSocket";

// =========================================================
// PROPS
// =========================================================

interface CustomersPageProps {
  selectedCustomer: Customer | null;

  onCustomerSelected: (
    customer: Customer | null,
  ) => void;
}

// =========================================================
// COMPONENT
// =========================================================

export default function CustomersPage({
  selectedCustomer,
  onCustomerSelected,
}: CustomersPageProps) {
  // =======================================================
  // STATE
  // =======================================================

  const [customers, setCustomers] =
    useState<Customer[]>([]);

  const [search, setSearch] =
    useState("");

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(null);

  const [
    showAddCustomer,
    setShowAddCustomer,
  ] = useState(false);

  // =======================================================
  // ADD CUSTOMER FORM
  // =======================================================

  const [newName, setNewName] =
    useState("");

  const [newPhone, setNewPhone] =
    useState("");

  const [
    newWhatsappId,
    setNewWhatsappId,
  ] = useState("");

  const [
    newMarketingOptedIn,
    setNewMarketingOptedIn,
  ] = useState(false);

  const [
    creating,
    setCreating,
  ] = useState(false);

  const [
    createError,
    setCreateError,
  ] = useState<string | null>(null);

  // =======================================================
  // LOAD CUSTOMERS
  // =======================================================

  const handleDashboardEvent = useCallback(
    (event: DashboardEvent) => {
      /*
      * --------------------------------------------------
      * CUSTOMER CREATED
      * --------------------------------------------------
      */
      if (
        event.type === "customer.created" &&
        event.customer
      ) {
        const newCustomer = event.customer as Customer;

        setCustomers((current) => {
          /*
          * Prevent duplicates.
          */
          if (
            current.some(
              (customer) =>
                customer.id === newCustomer.id,
            )
          ) {
            return current;
          }

          /*
          * If a search is active, don't blindly add the
          * customer because it may not match the search.
          *
          * The next normal search refresh will handle it.
          */
          if (search.trim()) {
            const searchText =
              search.trim().toLowerCase();

            const matches =
              newCustomer.name
                ?.toLowerCase()
                .includes(searchText) ||
              newCustomer.phone
                ?.toLowerCase()
                .includes(searchText);

            if (!matches) {
              return current;
            }
          }

          return [
            newCustomer,
            ...current,
          ];
        });

        /*
        * Automatically select newly created customer
        * when nothing is currently selected.
        */
        if (!selectedCustomer) {
          onCustomerSelected(newCustomer);
        }

        return;
      }

      /*
      * --------------------------------------------------
      * CUSTOMER UPDATED
      * --------------------------------------------------
      */
      if (
        event.type === "customer.updated" &&
        event.customer
      ) {
        const updatedCustomer =
          event.customer as Customer;

        setCustomers((current) => {
          const searchText = search.trim().toLowerCase();
          const matchesSearch = !searchText ||
            updatedCustomer.name?.toLowerCase().includes(searchText) ||
            updatedCustomer.phone?.toLowerCase().includes(searchText) ||
            updatedCustomer.whatsapp_id?.toLowerCase().includes(searchText);

          if (!matchesSearch) {
            return current.filter((customer) => customer.id !== updatedCustomer.id);
          }

          const exists = current.some((customer) => customer.id === updatedCustomer.id);
          if (!exists) return [updatedCustomer, ...current];

          return current.map((customer) =>
            customer.id === updatedCustomer.id ? updatedCustomer : customer,
          );
        });

        /*
        * Keep Business Operations panel synchronized.
        */
        if (
          selectedCustomer?.id ===
          updatedCustomer.id
        ) {
          onCustomerSelected(updatedCustomer);
        }

        return;
      }
    },
    [
      search,
      selectedCustomer,
      onCustomerSelected,
    ],
  );

  useDashboardWebSocket({
    onEvent: handleDashboardEvent,
  });

  const loadCustomers = useCallback(
    async () => {
      try {
        setLoading(true);
        setError(null);

        const data = await getCustomers({
          search: search.trim(),
          ordering: "-updated_at",
        });

        setCustomers(data);
      } catch (err) {
        console.error(
          "Unable to load customers:",
          err,
        );

        setError(
          "Unable to load customers. Please check the API.",
        );
      } finally {
        setLoading(false);
      }
    },
    [search],
  );

  // =======================================================
  // SEARCH / INITIAL LOAD
  //
  // Runs:
  // - on initial page load
  // - when search changes
  //
  // Does NOT run when customer selection changes.
  // =======================================================

  useEffect(() => {
    const timer =
      window.setTimeout(() => {
        void loadCustomers();
      }, 250);

    return () => {
      window.clearTimeout(timer);
    };
  }, [loadCustomers]);

  // =======================================================
  // SYNCHRONIZE SELECTED CUSTOMER
  //
  // This is deliberately separate from loadCustomers().
  //
  // Loading data may update the selected customer's object,
  // but updating the selection does not cause another fetch.
  // =======================================================

  useEffect(() => {
    if (customers.length === 0) {
      if (selectedCustomer) {
        const stillExists = customers.some(
          (customer) =>
            customer.id === selectedCustomer.id,
        );

        if (!stillExists) {
          onCustomerSelected(null);
        }
      }

      return;
    }

    // No customer selected:
    // select the first customer.
    if (!selectedCustomer) {
      onCustomerSelected(customers[0]);
      return;
    }

    // Customer is selected:
    // synchronize it with the latest API object.
    const refreshedCustomer =
      customers.find(
        (customer) =>
          customer.id === selectedCustomer.id,
      );

    if (refreshedCustomer) {
      // Only update the parent if the actual customer
      // object has changed.
      //
      // This prevents unnecessary parent updates.
      if (
        JSON.stringify(refreshedCustomer) !==
        JSON.stringify(selectedCustomer)
      ) {
        onCustomerSelected(
          refreshedCustomer,
        );
      }
    } else {
      // Selected customer is not in the current result.
      //
      // This commonly happens after a search.
      onCustomerSelected(
        customers[0],
      );
    }
  }, [
    customers,
    selectedCustomer,
    onCustomerSelected,
  ]);

  // =======================================================
  // SUMMARY
  // =======================================================

  const totalCustomers =
    customers.length;

  const optedInCustomers =
    useMemo(
      () =>
        customers.filter(
          (customer) =>
            customer.marketing_opted_in,
        ).length,
      [customers],
    );

  const activeCustomers =
    useMemo(
      () =>
        customers.filter(
          (customer) =>
            customer.is_active,
        ).length,
      [customers],
    );

  // =======================================================
  // RESET ADD FORM
  // =======================================================

  const resetAddForm =
    useCallback(() => {
      setNewName("");
      setNewPhone("");
      setNewWhatsappId("");
      setNewMarketingOptedIn(false);
      setCreateError(null);
    }, []);

  // =======================================================
  // OPEN ADD FORM
  // =======================================================

  const handleOpenAddCustomer =
    () => {
      resetAddForm();
      setShowAddCustomer(true);
    };

  // =======================================================
  // CLOSE ADD FORM
  // =======================================================

  const handleCloseAddCustomer =
    () => {
      if (creating) {
        return;
      }

      setShowAddCustomer(false);
      resetAddForm();
    };

  // =======================================================
  // CREATE CUSTOMER
  // =======================================================

  const handleCreateCustomer =
    async () => {
      const name =
        newName.trim();

      const phone =
        newPhone.trim();

      const whatsappId =
        newWhatsappId.trim();

      if (!name) {
        setCreateError(
          "Customer name is required.",
        );
        return;
      }

      if (!phone) {
        setCreateError(
          "Phone number is required.",
        );
        return;
      }

      try {
        setCreating(true);
        setCreateError(null);

        const customer =
          await createCustomer({
            name,
            phone,
            whatsapp_id:
              whatsappId || null,
            marketing_opted_in:
              newMarketingOptedIn,
            tags: [],
            custom_fields: {},
          });

        // Add/update immediately in the local list.
        //
        // This is an upsert because the WebSocket may have
        // already delivered customer.created before the POST
        // response arrives.
        setCustomers((current) => {
          const existingIndex = current.findIndex(
            (item) => item.id === customer.id,
          );

          if (existingIndex === -1) {
            return [
              customer,
              ...current,
            ];
          }

          const updated = [...current];
          updated[existingIndex] = customer;

          return updated;
        });

        // Select newly-created customer.
        onCustomerSelected(
          customer,
        );

        // Close modal.
        setShowAddCustomer(false);

        resetAddForm();
      } catch (err: any) {
        console.error(
          "Unable to create customer:",
          err,
        );

        const message =
          err?.response?.data
            ?.error?.message ??
          err?.response?.data
            ?.message ??
          err?.message ??
          "Unable to create customer.";

        setCreateError(message);
      } finally {
        setCreating(false);
      }
    };

  // =======================================================
  // RENDER
  // =======================================================

  return (
    <>
      <div className="customers-page">

        {/* =================================================
            HEADER
            ================================================= */}

        <div className="customers-page-header">

          <div>
            <h2>
              Customers
            </h2>

            <p>
              Manage your WhatsApp
              customers and their
              conversations.
            </p>
          </div>

          <div className="customers-header-actions">

            <button
              type="button"
              className="secondary-button"
              onClick={() =>
                void loadCustomers()
              }
              disabled={loading}
            >
              <RefreshCw
                size={15}
                className={
                  loading
                    ? "spin"
                    : ""
                }
              />

              Refresh
            </button>

            <button
              type="button"
              className="primary-button"
              onClick={
                handleOpenAddCustomer
              }
            >
              <UserPlus
                size={15}
              />

              Add Customer
            </button>

          </div>
        </div>

        {/* =================================================
            SUMMARY
            ================================================= */}

        <div className="customers-summary">

          <div className="customer-summary-card">

            <div className="customer-summary-icon">
              <Users
                size={17}
              />
            </div>

            <div>
              <span>
                Total Customers
              </span>

              <strong>
                {totalCustomers}
              </strong>
            </div>

          </div>

          <div className="customer-summary-card">

            <div className="customer-summary-icon">
              <MessageCircle
                size={17}
              />
            </div>

            <div>
              <span>
                Marketing Opt-In
              </span>

              <strong>
                {optedInCustomers}
              </strong>
            </div>

          </div>

          <div className="customer-summary-card">

            <div className="customer-summary-icon">
              <User
                size={17}
              />
            </div>

            <div>
              <span>
                Active Customers
              </span>

              <strong>
                {activeCustomers}
              </strong>
            </div>

          </div>

        </div>

        {/* =================================================
            SEARCH
            ================================================= */}

        <div className="customers-toolbar">

          <div className="customers-search">

            <Search
              size={16}
            />

            <input
              type="text"
              value={search}
              onChange={(
                event,
              ) =>
                setSearch(
                  event.target.value,
                )
              }
              placeholder="Search by name or phone..."
            />

          </div>

          {search && (
            <button
              type="button"
              className="customers-clear-search"
              onClick={() =>
                setSearch("")
              }
              aria-label="Clear search"
            >
              <X
                size={15}
              />
            </button>
          )}

        </div>

        {/* =================================================
            CUSTOMER LIST
            ================================================= */}

        <div className="customers-list">

          {loading &&
          customers.length === 0 ? (
            <div className="customers-empty">

              <RefreshCw
                size={24}
                className="spin"
              />

              <strong>
                Loading customers...
              </strong>

            </div>
          ) : error ? (
            <div className="customers-empty error">

              <strong>
                {error}
              </strong>

              <button
                type="button"
                className="secondary-button"
                onClick={() =>
                  void loadCustomers()
                }
              >
                Retry
              </button>

            </div>
          ) : customers.length === 0 ? (
            <div className="customers-empty">

              <Users
                size={30}
              />

              <strong>
                No customers found
              </strong>

              <span>
                Try a different
                search.
              </span>

            </div>
          ) : (
            customers.map(
              (customer) => (
                <button
                  type="button"
                  key={customer.id}
                  className={`customer-list-item ${
                    selectedCustomer?.id ===
                    customer.id
                      ? "active"
                      : ""
                  }`}
                  onClick={() =>
                    onCustomerSelected(
                      customer,
                    )
                  }
                >

                  {/* Avatar */}

                  <div className="customer-avatar">
                    {(
                      customer.name ||
                      customer.phone ||
                      "?"
                    )
                      .charAt(0)
                      .toUpperCase()}
                  </div>

                  {/* Customer information */}

                  <div className="customer-list-content">

                    <div className="customer-list-top">

                      <strong>
                        {customer.name ||
                          "Unnamed Customer"}
                      </strong>

                      <div className="customer-list-badges">

                        {customer.marketing_opted_in && (
                          <span className="customer-optin">
                            Opt-in
                          </span>
                        )}

                        <span
                          className={`customer-active-badge ${
                            customer.is_active
                              ? "active"
                              : "inactive"
                          }`}
                        >
                          {customer.is_active
                            ? "Active"
                            : "Inactive"}
                        </span>

                      </div>

                    </div>

                    <span className="customer-phone">
                      {customer.phone}
                    </span>

                  </div>

                </button>
              ),
            )
          )}

        </div>

      </div>

      {/* ===================================================
          ADD CUSTOMER MODAL
          =================================================== */}

      {showAddCustomer && (
        <div
          className="customer-modal-backdrop"
          onMouseDown={(
            event,
          ) => {
            if (
              event.target ===
              event.currentTarget
            ) {
              handleCloseAddCustomer();
            }
          }}
        >

          <div className="customer-modal">

            {/* Header */}

            <div className="customer-modal-header">

              <div>
                <h3>
                  Add Customer
                </h3>

                <p>
                  Create a new WhatsApp
                  customer.
                </p>
              </div>

              <button
                type="button"
                className="customer-modal-close"
                onClick={
                  handleCloseAddCustomer
                }
                disabled={creating}
              >
                <X
                  size={18}
                />
              </button>

            </div>

            {/* Form */}

            <div className="customer-modal-body">

              {createError && (
                <div className="customer-form-error">
                  {createError}
                </div>
              )}

              <div className="customer-form-group">

                <label>
                  Customer Name
                </label>

                <div className="customer-form-input">

                  <User
                    size={16}
                  />

                  <input
                    type="text"
                    value={newName}
                    onChange={(
                      event,
                    ) =>
                      setNewName(
                        event.target.value,
                      )
                    }
                    placeholder="Enter customer name"
                    autoFocus
                  />

                </div>

              </div>

              <div className="customer-form-group">

                <label>
                  Phone Number
                </label>

                <div className="customer-form-input">

                  <Phone
                    size={16}
                  />

                  <input
                    type="text"
                    value={newPhone}
                    onChange={(
                      event,
                    ) =>
                      setNewPhone(
                        event.target.value,
                      )
                    }
                    placeholder="e.g. 917738667200"
                  />

                </div>

              </div>

              <div className="customer-form-group">

                <label>
                  WhatsApp ID
                  <span>
                    Optional
                  </span>
                </label>

                <div className="customer-form-input">

                  <Smartphone
                    size={16}
                  />

                  <input
                    type="text"
                    value={
                      newWhatsappId
                    }
                    onChange={(
                      event,
                    ) =>
                      setNewWhatsappId(
                        event.target.value,
                      )
                    }
                    placeholder="WhatsApp ID"
                  />

                </div>

              </div>

              <label className="customer-checkbox-row">

                <input
                  type="checkbox"
                  checked={
                    newMarketingOptedIn
                  }
                  onChange={(
                    event,
                  ) =>
                    setNewMarketingOptedIn(
                      event.target.checked,
                    )
                  }
                />

                <span>
                  Customer has opted
                  in to marketing
                  messages
                </span>

              </label>

            </div>

            {/* Footer */}

            <div className="customer-modal-footer">

              <button
                type="button"
                className="secondary-button"
                onClick={
                  handleCloseAddCustomer
                }
                disabled={creating}
              >
                Cancel
              </button>

              <button
                type="button"
                className="primary-button"
                onClick={
                  handleCreateCustomer
                }
                disabled={creating}
              >
                {creating ? (
                  <>
                    <RefreshCw
                      size={15}
                      className="spin"
                    />

                    Creating...
                  </>
                ) : (
                  <>
                    <UserPlus
                      size={15}
                    />

                    Create Customer
                  </>
                )}
              </button>

            </div>

          </div>

        </div>
      )}

    </>
  );
}