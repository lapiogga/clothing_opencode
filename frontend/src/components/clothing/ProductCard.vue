<template>
  <div class="product-card" @click="$emit('click', product)">
    <div class="card-image">
      <img v-if="product.imageUrl" :src="product.imageUrl" :alt="product.name" />
      <div v-else class="image-placeholder">📷</div>
      <span v-if="product.salePrice" class="sale-badge">할인</span>
    </div>
    <div class="card-content">
      <div class="category">{{ product.category?.name }}</div>
      <div class="name">{{ product.name }}</div>
      <div class="code">{{ product.code }}</div>
      <div class="price">
        <span v-if="product.salePrice" class="original">
          {{ product.price?.toLocaleString() }}원
        </span>
        <span class="current">
          {{ (product.salePrice || product.price)?.toLocaleString() }}원
        </span>
      </div>
      <div class="point">{{ product.pointPrice?.toLocaleString() }}P</div>
      <div class="stock" :class="{ low: product.stock <= 10, out: product.stock === 0 }">
        재고: {{ product.stock }}
      </div>
    </div>
    <button class="add-cart-btn" @click.stop="$emit('add-cart', product)">
      장바구니 담기
    </button>
  </div>
</template>

<script setup>
defineProps({
  product: {
    type: Object,
    required: true
  }
})

defineEmits(['click', 'add-cart'])
</script>

<style scoped>
.product-card {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  cursor: pointer;
  transition: all 0.2s;
}

.product-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transform: translateY(-2px);
}

.card-image {
  position: relative;
  aspect-ratio: 1;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.image-placeholder {
  font-size: 48px;
}

.sale-badge {
  position: absolute;
  top: 8px;
  right: 8px;
  background: #dc2626;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.card-content {
  padding: 16px;
}

.category {
  font-size: 11px;
  color: #3b82f6;
  margin-bottom: 4px;
}

.name {
  font-weight: 500;
  margin-bottom: 4px;
  line-height: 1.4;
}

.code {
  font-size: 12px;
  color: #9ca3af;
  margin-bottom: 8px;
}

.price {
  margin-bottom: 4px;
}

.original {
  text-decoration: line-through;
  font-size: 12px;
  color: #9ca3af;
  margin-right: 6px;
}

.current {
  font-weight: 600;
  font-size: 16px;
}

.point {
  font-size: 13px;
  color: #3b82f6;
  margin-bottom: 8px;
}

.stock {
  font-size: 12px;
  color: #6b7280;
}

.stock.low {
  color: #f59e0b;
}

.stock.out {
  color: #dc2626;
}

.add-cart-btn {
  width: 100%;
  padding: 12px;
  background: #3b82f6;
  color: white;
  border: none;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.add-cart-btn:hover {
  background: #2563eb;
}
</style>
