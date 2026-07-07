use logistics;

select count(*) from shipments where status = 'Delivered';

select count(*) from shipments where status = 'Cancelled';

select avg(weight) from shipments;

select * from shipments order by weight desc limit 10;

SELECT courier_id, COUNT(*) AS total_shipments
FROM shipments
GROUP BY courier_id;

SELECT origin, COUNT(*) AS total_shipments
FROM shipments
GROUP BY origin
ORDER BY total_shipments DESC;

SELECT destination, COUNT(*) AS total_shipments
FROM shipments
GROUP BY destination
ORDER BY total_shipments DESC;

SELECT *
FROM shipments
WHERE delivery_date IS NULL;

SELECT AVG(rating)
FROM courier_staff;

SELECT
s.shipment_id,
s.origin,
s.destination,
c.name,
c.rating
FROM shipments s
JOIN courier_staff c
ON s.courier_id = c.courier_id;

SELECT
origin,
destination,
COUNT(*) AS total_shipments
FROM shipments
GROUP BY origin, destination
ORDER BY total_shipments DESC;



