-- Reservas del agente de Urban en Supabase (PostgreSQL).
-- Sigue el modelo ER de la semana 4: RESERVA 1..N LINEA_RESERVA.
-- Pegar completo en Supabase -> SQL Editor -> New query -> Run.

create table if not exists public.reserva (
  id             bigint generated always as identity primary key,
  numero         text not null unique,                 -- R-0001
  chat_id        text not null,                        -- conversación (web o WhatsApp)
  nombre_cliente text not null check (length(trim(nombre_cliente)) > 0),
  forma_pago     text not null
                 check (forma_pago in ('efectivo', 'nequi', 'daviplata', 'nu')),
  estado         text not null default 'reservada'
                 check (estado in ('reservada', 'pago_por_verificar', 'pagada',
                                   'entregada', 'vencida', 'cancelada')),
  total          integer not null check (total >= 40000),
  creada_en      timestamptz not null,
  vence_en       timestamptz,                          -- null si es transferencia
  pagada_en      timestamptz,
  cerrada_en     timestamptz
);

create table if not exists public.linea_reserva (
  id              bigint generated always as identity primary key,
  reserva_id      bigint not null references public.reserva (id) on delete cascade,
  codigo          text not null,
  color           text not null default '',
  talla           text not null,
  nombre_prenda   text not null,
  cantidad        integer not null check (cantidad between 1 and 5),
  precio_unitario integer not null check (precio_unitario >= 40000)
);

create index if not exists linea_reserva_reserva_id on public.linea_reserva (reserva_id);

-- Nadie entra con la clave pública: solo el servidor con la clave secreta.
alter table public.reserva enable row level security;
alter table public.linea_reserva enable row level security;

-- La reserva y su línea se guardan juntas (una transacción) o no se guardan.
create or replace function public.guardar_reserva(datos jsonb)
returns bigint
language plpgsql
set search_path = ''
as $$
declare
  nueva_id bigint;
begin
  insert into public.reserva
    (numero, chat_id, nombre_cliente, forma_pago, total, creada_en, vence_en)
  values
    (datos->>'numero', datos->>'chat_id', datos->>'nombre_cliente',
     datos->>'forma_pago', (datos->>'total')::integer,
     (datos->>'creada_en')::timestamptz, (datos->>'vence_en')::timestamptz)
  returning id into nueva_id;

  insert into public.linea_reserva
    (reserva_id, codigo, color, talla, nombre_prenda, cantidad, precio_unitario)
  values
    (nueva_id, datos->>'codigo', coalesce(datos->>'color', ''), datos->>'talla',
     datos->>'nombre_prenda', (datos->>'cantidad')::integer,
     (datos->>'precio_unitario')::integer);

  return nueva_id;
end;
$$;

revoke execute on function public.guardar_reserva(jsonb) from public, anon, authenticated;
grant execute on function public.guardar_reserva(jsonb) to service_role;
