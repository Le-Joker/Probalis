-- Probalis : comptes, Premium, paiements et journal des e-mails.
-- À coller une fois dans Supabase > SQL Editor (ou « supabase db push »). Voir docs/06-comptes-premium-emails.md.
--
-- Règle de sécurité : le téléphone (clé publique) ne peut lire et modifier QUE son propre profil, et seulement
-- les réglages. Le Premium (premium_until) n'est écrit que par les fonctions de paiement, avec la clé secrète.

-- ---------- Profils ----------
create table if not exists public.profiles (
  id               uuid primary key references auth.users (id) on delete cascade,
  email            text,
  name             text,
  avatar_url       text,
  lang             text not null default 'fr' check (lang in ('fr', 'en')),
  country          text check (country ~ '^[A-Z]{2}$'),
  tz               text check (char_length(tz) <= 64),
  is_adult         boolean not null default false,
  email_news       boolean not null default false,  -- alertes « grand choc demain » : à activer soi-même
  email_reminders  boolean not null default true,   -- rappel avant la fin du Premium
  favorite_leagues text[] not null default '{}' check (cardinality(favorite_leagues) <= 60),
  premium_until    timestamptz,
  welcome_sent_at  timestamptz,
  created_at       timestamptz not null default now(),
  updated_at       timestamptz not null default now()
);

alter table public.profiles enable row level security;

drop policy if exists "profil : lire le sien" on public.profiles;
create policy "profil : lire le sien" on public.profiles
  for select to authenticated using ((select auth.uid()) = id);

drop policy if exists "profil : modifier le sien" on public.profiles;
create policy "profil : modifier le sien" on public.profiles
  for update to authenticated using ((select auth.uid()) = id) with check ((select auth.uid()) = id);

revoke all on public.profiles from anon, authenticated;
grant select on public.profiles to authenticated;
grant update (lang, country, tz, is_adult, email_news, email_reminders, favorite_leagues) on public.profiles to authenticated;

create or replace function public.touch_updated_at() returns trigger
language plpgsql set search_path = '' as $$
begin
  new.updated_at := now();
  return new;
end $$;

drop trigger if exists profiles_touch on public.profiles;
create trigger profiles_touch before update on public.profiles
  for each row execute function public.touch_updated_at();

-- Un profil est créé à la première connexion Google (nom et photo du compte Google)
create or replace function public.handle_new_user() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  insert into public.profiles (id, email, name, avatar_url)
  values (new.id, new.email,
          coalesce(new.raw_user_meta_data ->> 'full_name', new.raw_user_meta_data ->> 'name'),
          coalesce(new.raw_user_meta_data ->> 'avatar_url', new.raw_user_meta_data ->> 'picture'))
  on conflict (id) do nothing;
  return new;
end $$;

drop trigger if exists on_auth_user_created on auth.users;
create trigger on_auth_user_created after insert on auth.users
  for each row execute function public.handle_new_user();

create or replace function public.sync_user_email() returns trigger
language plpgsql security definer set search_path = '' as $$
begin
  update public.profiles set email = new.email where id = new.id;
  return new;
end $$;

drop trigger if exists on_auth_user_email on auth.users;
create trigger on_auth_user_email after update of email on auth.users
  for each row execute function public.sync_user_email();

-- ---------- Paiements (pass de 7 ou 30 jours, sans abonnement) ----------
create table if not exists public.payments (
  id              uuid primary key default gen_random_uuid(),
  user_id         uuid references auth.users (id) on delete set null,  -- gardé pour la comptabilité si le compte est supprimé
  provider        text not null check (provider in ('stripe', 'flutterwave')),
  plan            text not null check (plan in ('week', 'month')),
  days            int  not null check (days between 1 and 366),
  currency        text not null check (currency ~ '^[A-Z]{3}$'),
  amount          numeric(12, 2) not null check (amount > 0),
  country         text,
  lang            text not null default 'fr',
  status          text not null default 'pending' check (status in ('pending', 'paid', 'failed', 'cancelled')),
  provider_ref    text,  -- Stripe : session de paiement ; Flutterwave : numéro de transaction
  created_at      timestamptz not null default now(),
  paid_at         timestamptz,
  receipt_sent_at timestamptz
);

create unique index if not exists payments_provider_ref on public.payments (provider, provider_ref) where provider_ref is not null;
create index if not exists payments_user on public.payments (user_id, created_at desc);

alter table public.payments enable row level security;
drop policy if exists "paiements : lire les siens" on public.payments;
create policy "paiements : lire les siens" on public.payments
  for select to authenticated using ((select auth.uid()) = user_id);
revoke all on public.payments from anon, authenticated;
grant select on public.payments to authenticated;

-- Active le Premium d'un paiement confirmé. Sans risque si on l'appelle deux fois (webhook + retour du site) :
-- le pass n'est ajouté qu'une fois. Un pass acheté pendant un Premium en cours s'ajoute à la suite.
create or replace function public.grant_premium(p_payment uuid, p_ref text default null)
returns table (user_id uuid, premium_until timestamptz, newly_paid boolean)
language plpgsql security definer set search_path = '' as $$
#variable_conflict use_column
declare
  pay public.payments%rowtype;
  new_until timestamptz;
begin
  select * into pay from public.payments where id = p_payment for update;
  if not found then
    raise exception 'paiement inconnu : %', p_payment;
  end if;
  if pay.status = 'paid' then
    return query select pay.user_id, (select pr.premium_until from public.profiles pr where pr.id = pay.user_id), false;
    return;
  end if;
  update public.payments
     set status = 'paid', paid_at = now(), provider_ref = coalesce(p_ref, provider_ref)
   where id = p_payment;
  if pay.user_id is not null then
    update public.profiles pr
       set premium_until = greatest(coalesce(pr.premium_until, now()), now()) + make_interval(days => pay.days)
     where pr.id = pay.user_id
     returning pr.premium_until into new_until;
  end if;
  return query select pay.user_id, new_until, true;
end $$;

revoke all on function public.grant_premium(uuid, text) from public, anon, authenticated;
grant execute on function public.grant_premium(uuid, text) to service_role;

-- ---------- Journal des e-mails : jamais deux fois le même e-mail ----------
create table if not exists public.email_log (
  id         bigint generated always as identity primary key,
  user_id    uuid not null references auth.users (id) on delete cascade,
  kind       text not null,          -- welcome, receipt, expiry, big_match
  ref        text not null default '',
  created_at timestamptz not null default now(),
  unique (user_id, kind, ref)
);
alter table public.email_log enable row level security;  -- aucune règle : seules les fonctions (clé secrète) y accèdent
revoke all on public.email_log from anon, authenticated;

-- ---------- Supprimer son compte (bouton « Supprimer mon compte ») ----------
create or replace function public.delete_my_account() returns void
language plpgsql security definer set search_path = '' as $$
declare
  uid uuid := auth.uid();
begin
  if uid is null then
    raise exception 'non connecté';
  end if;
  delete from auth.users where id = uid;  -- efface aussi le profil et le journal ; les paiements restent, anonymes
end $$;

revoke all on function public.delete_my_account() from public, anon;
grant execute on function public.delete_my_account() to authenticated;
