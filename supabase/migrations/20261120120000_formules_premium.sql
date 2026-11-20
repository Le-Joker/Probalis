-- Cinq formules Premium (2026-11-20) : pass de 7 jours, 30 jours, 3 mois (90 j), 6 mois (180 j) et 1 an (365 j).
-- Les prix et les durées restent dans supabase/functions/_shared/prices.json ; la base n'accepte que ces noms de formule.
alter table public.payments drop constraint if exists payments_plan_check;
alter table public.payments
  add constraint payments_plan_check check (plan in ('week', 'month', 'quarter', 'half', 'year'));
