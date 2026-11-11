import { motion, useReducedMotion } from 'framer-motion';

export default function MetricCard({ label, value, hint, trend, trendDir = 'up', icon: Icon }) {
  const reduce = useReducedMotion();
  return (
    <motion.article
      className="card card-pad"
      initial={reduce ? false : { opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
    >
      <div className="metric-label">
        <span>{label}</span>
        {Icon ? <Icon size={16} strokeWidth={1.75} /> : null}
      </div>
      <p className="metric-value">{value}</p>
      {trend ? <p className={`metric-trend ${trendDir}`}>{trend}</p> : null}
      {hint ? <p className="card-sub">{hint}</p> : null}
    </motion.article>
  );
}
