-- Probalis : récompenses, parrainage, cadeaux de l'admin, analyses offertes, notifications et journal admin.
-- À appliquer une fois (supabase db query -f, ou SQL Editor). Voir docs/07-recompenses-admin-notifications.md.
--
-- Règles :
--  - Le téléphone (clé publique) ne peut toujours modifier que ses réglages. Les analyses offertes, le parrainage,
--    les récompenses et le Premium ne sont écrits que par les fonctions (clé secrète) ou par les fonctions SQL
--    ci-dessous, qui vérifient chaque cas.
--  - Seul l'admin offre du Premium (fonction « admin », réservée aux adresses de ADMIN_EMAILS).
--  - Le parrainage rapporte des analyses de match, jamais du Premium. Le barème est dans settings.referral.

-- ---------- Profils : nouvelles colonnes ----------
alter table public.profiles
  add column if not exists ref_code       text,
  add column if not exists referred_by    uuid references public.profiles (id) on delete set null,
  add column if not exists bonus_analyses int not null default 0 check (bonus_analyses between 0 and 10000),
  add column if not exists extra_matches  text[] not null default '{}',  -- matchs ouverts avec une analyse offerte (60 derniers)
  add column if not exists last_seen      date,                          -- dernier jour d'utilisation (heure du téléphone)
  add column if not exists active_days    int not null default 0,        -- nombre de jours différents d'utilisation
  add column if not exists role           text not null default 'member' check (role in ('member', 'admin')),
  add column if not exists push_daily     boolean not null default true; -- notification « analyses du jour prêtes »

create unique index if not exists profiles_ref_code on public.profiles (ref_code);
create index if not exists profiles_referred_by on public.profiles (referred_by) where referred_by is not null;
create index if not exists profiles_created on public.profiles (created_at desc);

grant update (push_daily) on public.profiles to authenticated;

-- Code de parrainage : 6 caractères faciles à lire (sans 0/O, 1/I/L)
create or replace function public.new_ref_code() returns text
language plpgsql set search_path = '' as $$
declare
  abc constant text := 'ABCDEFGHJKMNPQRSTUVWXYZ23456789';
  code text;
begin
  loop
    code := '';
    for i in 1..6 loop
      code := code || substr(abc, 1 + floor(random() * length(abc))::int, 1);
    end loop;
    exit when not exists (select 1 from public.profiles p where p.ref_code = code);
  end loop;
  return code;
end $$;

revoke all on function public.new_ref_code() from public, anon, authenticated;

do $$
declare
  r record;
begin
  for r in select id from public.profiles where ref_code is null loop
    update public.profiles set ref_code = public.new_ref_code() where id = r.id;
  end loop;
end $$;

alter table public.profiles alter column ref_code set not null;

create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, email, name, avatar_url, ref_code)
  values (new.id, new.email,
          coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name'),
          coalesce(new.raw_user_meta_data ->> 'avatar_url', new.raw_user_meta_data ->> 'picture'),
          public.new_ref_code())
  on conflict (id) do nothing;
  return new;
end $$;

-- ---------- Réglages (barème du parrainage), lisibles par tous ----------
create table if not exists public.settings (
  key        text primary key,
  value      jsonb not null,
  updated_at timestamptz not null default now()
);
alter table public.settings enable row level security;
drop policy if exists "réglages : lecture publique" on public.settings;
create policy "réglages : lecture publique" on public.settings
  for select to anon, authenticated using (key in ('referral'));
revoke all on public.settings from anon, authenticated;
grant select on public.settings to anon, authenticated;

-- Analyses données : à l'inscription d'un ami, quand il a utilisé l'appli 3 jours différents, à chaque pass qu'il
-- achète (selon la durée), et un bonus de bienvenue pour l'ami. Au plus 10 amis récompensés par mois
-- (inscription et activité) ; les achats ne sont pas limités.
insert into public.settings (key, value) values ('referral', jsonb_build_object(
  'signup', 2, 'active', 3, 'active_days', 3, 'welcome', 2, 'monthly_cap', 10,
  'purchase', jsonb_build_object('week', 4, 'month', 5, 'quarter', 6, 'half', 8, 'year', 10)))
on conflict (key) do nothing;

-- Secrets générés par les fonctions (clés des notifications) : personne d'autre n'y a accès
create table if not exists public.app_secrets (
  key        text primary key,
  value      jsonb not null,
  created_at timestamptz not null default now()
);
alter table public.app_secrets enable row level security;
revoke all on public.app_secrets from anon, authenticated;

-- ---------- Récompenses ----------
-- Cadeau de l'admin : « sent » (e-mail envoyé) → le membre ouvre le lien de l'e-mail → « available » (visible dans
-- l'onglet Récompenses) → il l'active → « used ». Les récompenses du parrainage arrivent directement en « available ».
create table if not exists public.rewards (
  id          uuid primary key default gen_random_uuid(),
  user_id     uuid not null references auth.users (id) on delete cascade,
  kind        text not null check (kind in ('premium', 'analyses')),
  plan        text check (plan in ('week', 'month', 'quarter', 'half', 'year')),
  days        int check (days between 1 and 366),
  amount      int check (amount between 1 and 100),
  source      text not null check (source in ('gift', 'referral_signup', 'referral_active', 'referral_purchase', 'welcome_bonus')),
  ref         text not null default '',  -- ami concerné, paiement… (jamais deux fois la même récompense)
  note        text check (char_length(note) <= 280),
  status      text not null default 'available' check (status in ('sent', 'available', 'used', 'expired', 'cancelled')),
  claim_hash  text,                      -- empreinte du lien de l'e-mail (le lien lui-même n'est gardé nulle part)
  created_by  uuid references auth.users (id) on delete set null,
  created_at  timestamptz not null default now(),
  expires_at  timestamptz,
  claimed_at  timestamptz,
  used_at     timestamptz,
  notified_at timestamptz,
  check ((kind = 'premium' and plan is not null and days is not null) or (kind = 'analyses' and amount is not null))
);
create unique index if not exists rewards_once on public.rewards (user_id, source, ref) where source <> 'gift';
create index if not exists rewards_user on public.rewards (user_id, created_at desc);
create index if not exists rewards_recent on public.rewards (created_at desc);

alter table public.rewards enable row level security;
drop policy if exists "récompenses : voir les siennes" on public.rewards;
create policy "récompenses : voir les siennes" on public.rewards
  for select to authenticated using ((select auth.uid()) = user_id and status <> 'sent');
revoke all on public.rewards from anon, authenticated;
grant select (id, kind, plan, days, amount, source, note, status, created_at, expires_at, claimed_at, used_at)
  on public.rewards to authenticated;

-- ---------- Paiements : paiement reçu à la main (WhatsApp) ----------
alter table public.payments drop constraint if exists payments_provider_check;
alter table public.payments
  add constraint payments_provider_check check (provider in ('stripe', 'flutterwave', 'manual'));
alter table public.payments
  add column if not exists created_by uuid references auth.users (id) on delete set null,
  add column if not exists note       text check (char_length(note) <= 280);

-- ---------- Journal de l'admin ----------
create table if not exists public.admin_log (
  id         bigint generated always as identity primary key,
  admin_id   uuid references auth.users (id) on delete set null,
  action     text not null,
  target     uuid,
  detail     jsonb not null default '{}',
  created_at timestamptz not null default now()
);
create index if not exists admin_log_recent on public.admin_log (created_at desc);
alter table public.admin_log enable row level security;
revoke all on public.admin_log from anon, authenticated;

-- ---------- Notifications (abonnements des téléphones) ----------
create table if not exists public.push_subs (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users (id) on delete cascade,
  endpoint   text not null unique check (endpoint ~ '^https://' and char_length(endpoint) <= 1000),
  p256dh     text not null check (char_length(p256dh) <= 200),
  auth       text not null check (char_length(auth) <= 100),
  lang       text not null default 'fr' check (lang in ('fr', 'en')),
  created_at timestamptz not null default now(),
  last_ok    timestamptz,
  fails      int not null default 0
);
create index if not exists push_subs_user on public.push_subs (user_id);
alter table public.push_subs enable row level security;
revoke all on public.push_subs from anon, authenticated;

-- ---------- Parrainage ----------
-- Reste-t-il de la place ce mois-ci pour récompenser cet ami ? (un ami déjà récompensé ce mois-ci compte une fois)
create or replace function public.referral_room(p_sponsor uuid, p_friend uuid) returns boolean
language sql stable security definer set search_path = '' as $$
  with month as (
    select distinct r.ref from public.rewards r
     where r.user_id = p_sponsor and r.source in ('referral_signup', 'referral_active')
       and r.created_at >= date_trunc('month', now())
  )
  select exists (select 1 from month where ref = p_friend::text)
      or (select count(*) from month) < coalesce(
           (select (s.value ->> 'monthly_cap')::int from public.settings s where s.key = 'referral'), 10);
$$;

-- Lie un nouveau compte à son parrain (code du lien d'invitation). Renvoie les récompenses créées.
-- Seulement pour un compte de moins de 3 jours, une seule fois, et jamais son propre code.
create or replace function public.referral_attach(p_user uuid, p_code text) returns setof uuid
language plpgsql security definer set search_path = '' as $$
declare
  me public.profiles%rowtype;
  sponsor uuid;
  cfg jsonb := coalesce((select s.value from public.settings s where s.key = 'referral'), '{}'::jsonb);
  n int;
  rid uuid;
begin
  select * into me from public.profiles where id = p_user for update;
  if not found or me.referred_by is not null or me.created_at < now() - interval '3 days' then
    return;
  end if;
  select p.id into sponsor from public.profiles p where p.ref_code = upper(trim(coalesce(p_code, '')));
  if sponsor is null or sponsor = p_user then
    return;
  end if;
  update public.profiles set referred_by = sponsor where id = p_user;

  n := coalesce((cfg ->> 'welcome')::int, 0);
  if n > 0 then
    insert into public.rewards (user_id, kind, amount, source, ref)
    values (p_user, 'analyses', least(n, 100), 'welcome_bonus', '')
    on conflict (user_id, source, ref) where source <> 'gift' do nothing
    returning id into rid;
    if rid is not null then return next rid; end if;
  end if;

  n := coalesce((cfg ->> 'signup')::int, 0);
  if n > 0 and public.referral_room(sponsor, p_user) then
    rid := null;
    insert into public.rewards (user_id, kind, amount, source, ref)
    values (sponsor, 'analyses', least(n, 100), 'referral_signup', p_user::text)
    on conflict (user_id, source, ref) where source <> 'gift' do nothing
    returning id into rid;
    if rid is not null then return next rid; end if;
  end if;
end $$;

-- Note un jour d'utilisation (une fois par jour). Au 3e jour différent, le parrain reçoit sa récompense.
create or replace function public.activity_ping(p_user uuid, p_day date) returns setof uuid
language plpgsql security definer set search_path = '' as $$
declare
  today date := (now() at time zone 'utc')::date;
  cfg jsonb := coalesce((select s.value from public.settings s where s.key = 'referral'), '{}'::jsonb);
  days_n int;
  sponsor uuid;
  n int;
  rid uuid;
begin
  if p_day is null or p_day < today - 1 or p_day > today + 1 then
    raise exception 'date invalide';
  end if;
  update public.profiles
     set last_seen = p_day, active_days = active_days + 1
   where id = p_user and (last_seen is null or last_seen < p_day)
   returning active_days, referred_by into days_n, sponsor;
  if not found or sponsor is null then
    return;
  end if;
  n := coalesce((cfg ->> 'active')::int, 0);
  if n > 0 and days_n >= coalesce((cfg ->> 'active_days')::int, 3) and public.referral_room(sponsor, p_user) then
    insert into public.rewards (user_id, kind, amount, source, ref)
    values (sponsor, 'analyses', least(n, 100), 'referral_active', p_user::text)
    on conflict (user_id, source, ref) where source <> 'gift' do nothing
    returning id into rid;
    if rid is not null then return next rid; end if;
  end if;
end $$;

-- ---------- Paiement confirmé : Premium + récompense du parrain ----------
-- Même comportement qu'avant (une seule fois par paiement, le pass s'ajoute à la suite), plus la récompense
-- du parrain selon la durée du pass. Renvoie aussi l'identifiant de cette récompense (pour l'e-mail).
drop function if exists public.grant_premium(uuid, text);
create function public.grant_premium(p_payment uuid, p_ref text default null)
returns table (user_id uuid, premium_until timestamptz, newly_paid boolean, reward_id uuid)
language plpgsql security definer set search_path = '' as $$
#variable_conflict use_column
declare
  pay public.payments%rowtype;
  new_until timestamptz;
  sponsor uuid;
  n int;
  rid uuid;
begin
  select * into pay from public.payments where id = p_payment for update;
  if not found then
    raise exception 'paiement inconnu : %', p_payment;
  end if;
  if pay.status = 'paid' then
    return query select pay.user_id, (select pr.premium_until from public.profiles pr where pr.id = pay.user_id), false, null::uuid;
    return;
  end if;
  update public.payments
     set status = 'paid', paid_at = now(), provider_ref = coalesce(p_ref, provider_ref)
   where id = p_payment;
  if pay.user_id is not null then
    update public.profiles pr
       set premium_until = greatest(coalesce(pr.premium_until, now()), now()) + make_interval(days => pay.days)
     where pr.id = pay.user_id
     returning pr.premium_until, pr.referred_by into new_until, sponsor;
    n := coalesce((select (s.value -> 'purchase' ->> pay.plan)::int from public.settings s where s.key = 'referral'), 0);
    if sponsor is not null and n > 0 then
      insert into public.rewards (user_id, kind, amount, source, ref)
      values (sponsor, 'analyses', least(n, 100), 'referral_purchase', pay.id::text)
      on conflict (user_id, source, ref) where source <> 'gift' do nothing
      returning id into rid;
    end if;
  end if;
  return query select pay.user_id, new_until, true, rid;
end $$;

revoke all on function public.grant_premium(uuid, text) from public, anon, authenticated;
grant execute on function public.grant_premium(uuid, text) to service_role;

-- ---------- Récompenses : valider le lien de l'e-mail, puis activer ----------
-- Lien de l'e-mail ouvert : le cadeau passe dans l'onglet Récompenses
create or replace function public.claim_reward(p_user uuid, p_id uuid, p_token text)
returns table (status text, kind text)
language plpgsql security definer set search_path = '' as $$
#variable_conflict use_column
declare
  r public.rewards%rowtype;
begin
  select * into r from public.rewards where id = p_id for update;
  if not found then
    raise exception 'unknown';
  end if;
  if r.user_id <> p_user then
    raise exception 'other_account';
  end if;
  if r.status = 'sent' then
    if r.expires_at is not null and r.expires_at < now() then
      update public.rewards set status = 'expired' where id = p_id;
      return query select 'expired'::text, r.kind;
      return;
    end if;
    if r.claim_hash is null or p_token is null
       or encode(sha256(convert_to(p_token, 'UTF8')), 'hex') <> r.claim_hash then
      raise exception 'bad_link';
    end if;
    update public.rewards set status = 'available', claimed_at = now(), claim_hash = null where id = p_id;
    return query select 'available'::text, r.kind;
    return;
  end if;
  return query select r.status, r.kind;
end $$;

-- Le membre active sa récompense : Premium prolongé, ou analyses ajoutées à son compteur
create or replace function public.apply_reward(p_user uuid, p_id uuid)
returns table (kind text, plan text, days int, amount int, premium_until timestamptz, bonus_analyses int, applied boolean)
language plpgsql security definer set search_path = '' as $$
#variable_conflict use_column
declare
  r public.rewards%rowtype;
  pu timestamptz;
  ba int;
begin
  select * into r from public.rewards where id = p_id for update;
  if not found or r.user_id <> p_user then
    raise exception 'unknown';
  end if;
  if r.status = 'used' then
    select pr.premium_until, pr.bonus_analyses into pu, ba from public.profiles pr where pr.id = p_user;
    return query select r.kind, r.plan, r.days, r.amount, pu, ba, false;
    return;
  end if;
  if r.status <> 'available' then
    raise exception 'not_available';
  end if;
  update public.rewards set status = 'used', used_at = now() where id = p_id;
  if r.kind = 'premium' then
    update public.profiles pr
       set premium_until = greatest(coalesce(pr.premium_until, now()), now()) + make_interval(days => r.days)
     where pr.id = p_user returning pr.premium_until, pr.bonus_analyses into pu, ba;
  else
    update public.profiles pr
       set bonus_analyses = least(pr.bonus_analyses + r.amount, 10000)
     where pr.id = p_user returning pr.premium_until, pr.bonus_analyses into pu, ba;
  end if;
  return query select r.kind, r.plan, r.days, r.amount, pu, ba, true;
end $$;

-- ---------- Analyse offerte : ouvrir un match de son choix ----------
-- Appelée directement par le téléphone. Le match reste ouvert (le gardien le lit dans extra_matches).
create or replace function public.use_bonus_analysis(p_match text)
returns table (bonus_analyses int, extra_matches text[])
language plpgsql security definer set search_path = '' as $$
#variable_conflict use_column
declare
  uid uuid := auth.uid();
begin
  if uid is null then
    raise exception 'non connecté';
  end if;
  if p_match is null or p_match !~ '^[a-z0-9-]{1,160}$' then
    raise exception 'match invalide';
  end if;
  update public.profiles pr
     set bonus_analyses = pr.bonus_analyses - 1,
         extra_matches = (array_append(pr.extra_matches, p_match))[greatest(1, cardinality(pr.extra_matches) - 58):]
   where pr.id = uid and pr.bonus_analyses > 0 and not (p_match = any (pr.extra_matches));
  if not found and not exists (select 1 from public.profiles pr where pr.id = uid and p_match = any (pr.extra_matches)) then
    raise exception 'plus d''analyse offerte';
  end if;
  return query select pr.bonus_analyses, pr.extra_matches from public.profiles pr where pr.id = uid;
end $$;

revoke all on function public.use_bonus_analysis(text) from public, anon;
grant execute on function public.use_bonus_analysis(text) to authenticated;

-- ---------- Admin : chiffres du tableau de bord et liste des membres ----------
create or replace function public.admin_stats() returns jsonb
language sql stable security definer set search_path = '' as $$
  select jsonb_build_object(
    'members',        (select count(*) from public.profiles),
    'new_today',      (select count(*) from public.profiles where created_at >= date_trunc('day', now())),
    'new_7d',         (select count(*) from public.profiles where created_at >= now() - interval '7 days'),
    'active_7d',      (select count(*) from public.profiles where last_seen >= (now() at time zone 'utc')::date - 6),
    'premium',        (select count(*) from public.profiles where premium_until > now()),
    'push',           (select count(distinct user_id) from public.push_subs),
    'referred_30d',   (select count(*) from public.profiles where referred_by is not null and created_at >= now() - interval '30 days'),
    'payments_30d',   (select count(*) from public.payments where status = 'paid' and paid_at >= now() - interval '30 days'),
    'revenue_30d',    (select coalesce(jsonb_object_agg(currency, total), '{}'::jsonb) from (
                        select currency, sum(amount) as total from public.payments
                         where status = 'paid' and paid_at >= now() - interval '30 days' group by currency) t),
    'gifts_pending',  (select count(*) from public.rewards where status = 'sent'),
    'rewards_open',   (select count(*) from public.rewards where status = 'available'),
    'rewards_30d',    (select count(*) from public.rewards where created_at >= now() - interval '30 days'),
    'emails_today',   (select count(*) from public.email_log where created_at >= date_trunc('day', now())),
    'emails_30d',     (select count(*) from public.email_log where created_at >= now() - interval '30 days'),
    'signups_14d',    (select jsonb_agg(jsonb_build_object('d', d::date, 'n', (
                          select count(*) from public.profiles p
                           where p.created_at >= d and p.created_at < d + interval '1 day')) order by d)
                         from generate_series(date_trunc('day', now()) - interval '13 days', date_trunc('day', now()),
                                              interval '1 day') as d)
  );
$$;

create or replace function public.admin_members(p_q text default '', p_filter text default 'all', p_limit int default 30,
                                                p_offset int default 0)
returns table (id uuid, email text, name text, avatar_url text, country text, lang text, premium_until timestamptz,
               bonus_analyses int, created_at timestamptz, last_seen date, active_days int, ref_code text,
               referred_by_name text, referrals bigint, role text, push boolean, total bigint)
language sql stable security definer set search_path = '' as $$
  with base as (
    select p.* from public.profiles p
     where (coalesce(p_q, '') = '' or p.email ilike '%' || p_q || '%' or p.name ilike '%' || p_q || '%'
            or p.ref_code = upper(p_q))
       and (p_filter = 'all'
            or (p_filter = 'premium' and p.premium_until > now())
            or (p_filter = 'free' and (p.premium_until is null or p.premium_until <= now()))
            or (p_filter = 'referred' and p.referred_by is not null))
  )
  select b.id, b.email, b.name, b.avatar_url, b.country, b.lang, b.premium_until, b.bonus_analyses, b.created_at,
         b.last_seen, b.active_days, b.ref_code,
         (select s.name from public.profiles s where s.id = b.referred_by),
         (select count(*) from public.profiles f where f.referred_by = b.id),
         b.role,
         exists (select 1 from public.push_subs ps where ps.user_id = b.id),
         count(*) over ()
    from base b
   order by b.created_at desc
   limit least(greatest(p_limit, 1), 100) offset greatest(p_offset, 0);
$$;

-- Ces fonctions ne sont appelées que par les fonctions Probalis (clé secrète)
revoke all on function public.referral_room(uuid, uuid) from public, anon, authenticated;
revoke all on function public.referral_attach(uuid, text) from public, anon, authenticated;
revoke all on function public.activity_ping(uuid, date) from public, anon, authenticated;
revoke all on function public.claim_reward(uuid, uuid, text) from public, anon, authenticated;
revoke all on function public.apply_reward(uuid, uuid) from public, anon, authenticated;
revoke all on function public.admin_stats() from public, anon, authenticated;
revoke all on function public.admin_members(text, text, int, int) from public, anon, authenticated;
grant execute on function public.referral_room(uuid, uuid) to service_role;
grant execute on function public.referral_attach(uuid, text) to service_role;
grant execute on function public.activity_ping(uuid, date) to service_role;
grant execute on function public.claim_reward(uuid, uuid, text) to service_role;
grant execute on function public.apply_reward(uuid, uuid) to service_role;
grant execute on function public.admin_stats() to service_role;
grant execute on function public.admin_members(text, text, int, int) to service_role;
