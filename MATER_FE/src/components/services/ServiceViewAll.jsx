import React, { useEffect, useState, useMemo } from 'react';
import { useTable, useSortBy, useFilters } from 'react-table';
import { matchSorter } from 'match-sorter';
import '../common/common.css';
import '../common/Modal.css';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const DefaultColumnFilter = ({ column: { filterValue, preFilteredRows, setFilter } }) => {
  const count = preFilteredRows.length;
  return (
    <input
      value={filterValue || ''}
      onChange={(e) => {
        setFilter(e.target.value || undefined);
      }}
      placeholder={`Search ${count} records...`}
    />
  );
};

const fuzzyTextFilterFn = (rows, id, filterValue) => {
  return matchSorter(rows, filterValue, { keys: [row => row.values[id]] });
};

fuzzyTextFilterFn.autoRemove = val => !val;

const ServiceTable = ({ services }) => {
  const columns = useMemo(
    () => [
      {
        Header: 'ID',
        accessor: 'id',
      },
      {
        Header: 'Asset Name',
        accessor: 'asset_name',
        Filter: DefaultColumnFilter,
        filter: 'fuzzyText',
      },
      {
        Header: 'Service Type',
        accessor: 'service_type',
        Filter: DefaultColumnFilter,
        filter: 'fuzzyText',
      },
      {
        Header: 'Service Date',
        accessor: 'service_date',
        Filter: DefaultColumnFilter,
        filter: 'fuzzyText',
      },
      {
        Header: 'Service Status',
        accessor: 'service_status',
        Filter: DefaultColumnFilter,
        filter: 'fuzzyText',
      },
      {
        Header: 'Actions',
        Cell: ({ row }) => (
          <div>
            {/* Add actions as needed */}
          </div>
        ),
        disableFilters: true,
        disableSortBy: true,
      },
    ],
    []
  );

  const defaultColumn = useMemo(() => ({
    Filter: DefaultColumnFilter,
  }), []);

  const {
    getTableProps,
    getTableBodyProps,
    headerGroups,
    rows,
    prepareRow,
  } = useTable(
    {
      columns,
      data: services,
      defaultColumn,
      filterTypes: {
        fuzzyText: fuzzyTextFilterFn,
      },
    },
    useFilters,
    useSortBy
  );

  return (
    <div style={{ maxHeight: '90vh', overflowY: 'auto' }}>
      <table {...getTableProps()} className="standard-table">
        <thead>
          {headerGroups.map(headerGroup => (
            <tr {...headerGroup.getHeaderGroupProps()}>
              {headerGroup.headers.map(column => (
                <th {...column.getHeaderProps()} style={{ position: 'relative' }}>
                  <div {...column.getSortByToggleProps()} style={{ display: 'inline-block', cursor: 'pointer' }}>
                    {column.render('Header')}
                    {column.isSorted ? (column.isSortedDesc ? ' 🔽' : ' 🔼') : ''}
                  </div>
                  <div>{column.canFilter ? column.render('Filter') : null}</div>
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody {...getTableBodyProps()}>
          {rows.map(row => {
            prepareRow(row);
            return (
              <tr {...row.getRowProps()}>
                {row.cells.map(cell => (
                  <td {...cell.getCellProps()} style={{ padding: '10px', border: 'solid 1px gray' }}>
                    {cell.render('Cell')}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

const ServiceViewAll = () => {
  const [services, setServices] = useState([]);
  const [needsFetch, setNeedsFetch] = useState(true);
  const [isFetching, setIsFetching] = useState(false);

  const fetchServices = async () => {
    if (isFetching) return; // Prevent duplicate fetch calls
    setIsFetching(true);

    const jwtToken = localStorage.getItem('jwt'); // Retrieve JWT from local storage
    const baseUrl = import.meta.env.VITE_BASE_URL;

    try {
      const response = await fetch(`${baseUrl}/services/service_all`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ jwt: jwtToken }) // Send JWT in the body
      });

      // Check if response is JSON
      const contentType = response.headers.get("content-type");
      if (contentType && contentType.includes("application/json")) {
        const data = await response.json();
        if (response.ok) {
          setServices(data.services); 
          toast.success("Services successfully fetched!");
          console.log("Fetched services:", data.services);
        } else {
          toast.error(`Failed to fetch services: ${data.error}`);
          console.error('Failed to fetch services:', data.error);
        }
      } else {
        const text = await response.text();
        toast.error('Failed to fetch services: Invalid response format');
        console.error('Received non-JSON response:', text);
      }
    } catch (error) {
      toast.error(`Failed to fetch services: ${error.message}`);
      console.error('Failed to fetch services:', error.message);
    } finally {
      setIsFetching(false);
    }
  };

  useEffect(() => {
    if (needsFetch) {
      const timer = setTimeout(() => {
        fetchServices().then(() => setNeedsFetch(false)); // Reset after fetching
      }, 120); // Add a delay to debounce (120ms here)
  
      return () => clearTimeout(timer); // Clean up the timer
    }
  }, [needsFetch]);

  return (
    <div id="content">
      <h3>All Services</h3>
      {/* Counter showing total number of services */}
      <div className="counter">
        Total Services: {services.length}
      </div>
      <ServiceTable services={services} />
      <ToastContainer />
    </div>
  );
};

export default ServiceViewAll;
